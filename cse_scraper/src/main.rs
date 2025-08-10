mod module_bindings;
mod cse_scraper_state;
mod cse_scraper_get_regions;
mod cse_scraper_get_constellations;
use module_bindings::*;
use cse_common::*;
use spacetimedb_sdk::DbContext;
use tokio;
use cse_common::cse_substate::*;
use reqwest::Client;
use crate::cse_scraper_state::ResourceScrapeState;
use crate::cse_scraper_state::CSEScraperState;
use crate::cse_scraper_state::G_DB_CONN;
use crate::cse_scraper_state::G_SCRAPER_STATE;

fn on_versions_applied(ctx: &SubscriptionEventContext) -> ()
{
  println!("Fetched versions from DB {}{}", file!(), line!());
  let mut scraper_state = cse_scraper_state::G_SCRAPER_STATE.lock().unwrap();
  if scraper_state.versions_state.get_state() == ResourceScrapeState::RetrievingFromDB
  {
    scraper_state.versions_state.set_state(ResourceScrapeState::RetrievedFromDB);
  }
}

fn on_versions_error(ctx: &ErrorContext, error: spacetimedb_sdk::Error) -> ()
{
  panic!("Failed to fetch versions");
}

fn on_regions_applied(ctx: &SubscriptionEventContext) -> ()
{
  println!("Fetched regions from DB {}{}", file!(), line!());
  let mut scraper_state = cse_scraper_state::G_SCRAPER_STATE.lock().unwrap();
  if scraper_state.regions_state.get_state() == ResourceScrapeState::RetrievingFromDB
  {
    scraper_state.regions_state.set_state(ResourceScrapeState::RetrievedFromDB);
  }
}

fn on_regions_error(ctx: &ErrorContext, error: spacetimedb_sdk::Error) -> ()
{
  panic!("Failed to fetch regions from db");
}

fn on_constellations_applied(ctx: &SubscriptionEventContext) -> ()
{
  println!("Fetched constellations from DB {}{}", file!(), line!());
  let mut scraper_state = cse_scraper_state::G_SCRAPER_STATE.lock().unwrap();
  if scraper_state.constellations_state.get_state() == ResourceScrapeState::RetrievingFromDB
  {
    scraper_state.constellations_state.set_state(ResourceScrapeState::RetrievedFromDB);
  }
}

fn on_constellations_error(ctx: &ErrorContext, error: spacetimedb_sdk::Error) -> ()
{
  panic!("Failed to fetch constellations from db");
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>>
{
  {
    let ctx = G_DB_CONN.lock().unwrap();
    // subscribe to version
    ctx
    .subscription_builder()
    .on_applied
    (|ctx| -> () 
    {
      on_versions_applied(ctx);
      return ();
    })
    .on_error(on_versions_error)
    .subscribe(["SELECT * from version"]);

    // subscribe to region
    ctx
    .subscription_builder()
    .on_applied
    (|ctx| -> () 
    {
      on_regions_applied(ctx);
      return ();
    })
    .on_error(on_regions_error)
    .subscribe(["SELECT * from regions"]);

    // subscribe to constellations
    ctx
    .subscription_builder()
    .on_applied
    (|ctx| -> () 
    {
      on_constellations_applied(ctx);
      return ();
    })
    .on_error(on_constellations_error)
    .subscribe(["SELECT * from constellations"]);


    // start db thread
    ctx.run_threaded();
  }

  let client = Client::new();

  // Main loop
  while true
  {
    let mut tasks = Vec::<cse_common::AsyncAnyFunction>::new();
    {
      let unwrapped_state = G_SCRAPER_STATE.lock().unwrap();
      let mut local_scrape_state: CSEScraperState = unwrapped_state.clone();
      std::mem::drop(unwrapped_state);

      if local_scrape_state.versions_state.get_state() == ResourceScrapeState::RetrievedFromDB
      {
        let ctx = G_DB_CONN.lock().unwrap();
        // Check the universe version
        if let Some(eve_universe_version) = ctx.db.version().version_name().find(&cse_common::VERSION_NAME_EVE_UNIVERSE.to_string())
        {
          if eve_universe_version.version_value == VERSION_EVE_UNIVERSE
          {
            local_scrape_state.universe_version_valid = true;
          }
          else 
          {
            local_scrape_state.universe_version_valid = false; 
          }
        }
        else
        {
          local_scrape_state.universe_version_valid = false;
        }

        // Universe version is not valid, need to retrieve everything from eve servers
        if !local_scrape_state.universe_version_valid
        {
          if local_scrape_state.regions_state.get_state() == ResourceScrapeState::RetrievedFromDB
          {
            tasks.push(|| Box::pin(cse_scraper_get_regions::get_regions()));
            local_scrape_state.regions_state.set_state(ResourceScrapeState::RetrievingFromEveServers);
          }
        }
        // Universe version is valid, wait until we have got it from our db
        else
        {
          if local_scrape_state.regions_state.get_state() == ResourceScrapeState::RetrievedFromDB
          {
            local_scrape_state.regions_state.set_state(ResourceScrapeState::Valid);
          }
        }
      }
    }

    // Execute any tasks that've been queued together
    let mut futures = Vec::new();
    for task in tasks.iter()
    {
      futures.push(task());
    }

    futures::future::join_all(futures).await;
  } // Main loop end

  Ok(())
}