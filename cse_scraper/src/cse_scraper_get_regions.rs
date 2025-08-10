use cse_http_helpers;
use cse_common::{cse_substate::CSESubstateTrait};
use serde::{Serialize, Deserialize};
use crate::{cse_scraper_state::{ResourceScrapeState, G_DB_CONN, G_SCRAPER_STATE}, module_bindings::add_region};

#[derive(Serialize, Deserialize, Debug)]
pub struct EVERegion
{
  pub region_id: i64,
  pub name: String,
  pub description: Option<String>,
  pub constellations: Vec<i64>
}

async fn get_regions_helper(region_ids: Vec<i64>)
{
  // Set up the futures for fetching the urls
  let mut url_futures = Vec::new();
  for region_id in region_ids.iter()
  {
    let mut url =  String::from(cse_common::URL_EVE_REGIONS);
    url.push_str(region_id.to_string().as_str());
    url.push('/');

    let fetch_future = cse_http_helpers::get_url_text(url);
    url_futures.push(fetch_future);
  }
  
  let url_futures_results = futures::future::join_all(url_futures).await;
  let mut all_regions = Vec::new();
  for url_futures_result in url_futures_results.iter()
  {
    match url_futures_result  
    {
      Ok(region_text) =>
      {
        let region_result = serde_json::from_str::<EVERegion>(region_text.as_str());
        match region_result
        {
          Ok(region) =>
          {
            all_regions.push(region);
          }

          Err(e) =>
          {
            eprintln!("Error {}{}{}", e, file!(), line!());
            return;
          }
        }
      }

      Err(e) =>
      {
        eprintln!("Error {}{}{}", e, file!(), line!());
        continue;
      }
    }
  }

  for region in all_regions.iter()
  {
    let mut description = String::from("None");
    match &region.description
    {
      Some(descr) =>
      {
        description = descr.clone();
      }

      None =>
      {

      }
    }
    let db_res = G_DB_CONN.lock().unwrap().reducers.add_region(region.region_id, region.name.clone(), description);
    match db_res
    {
      Ok(res) =>
      {
      }

      Err(e) =>
      {
        eprintln!("Error {}{}{}", e, file!(), line!());
        return;
      }
    }
  }

  G_SCRAPER_STATE.lock().unwrap().regions_state.set_state(ResourceScrapeState::Valid);
  println!("Fetched regions from eve servers {}{}", file!(), line!());
}

pub async fn get_regions()
{
  println!("Fetching regions from eve servers {}{}", file!(), line!());
  let fetch_result = cse_http_helpers::get_url_text(cse_common::URL_EVE_REGIONS.to_string()).await;
  match fetch_result
  {
    Ok(region_ids_string) =>
    {
      let region_ids_result: Result<Vec<i64>, serde_json::Error> = serde_json::from_str(region_ids_string.as_str());
      match region_ids_result
      {
        Ok(region_ids) =>
        {
          get_regions_helper(region_ids).await;
        }

        Err(e) =>
        {
          eprintln!("Error {}{}{}", e, file!(), line!());
        }
      }

    }

    Err(e) =>
    {
      eprintln!("Error {}{}{}", e, file!(), line!());
    }
  }
}