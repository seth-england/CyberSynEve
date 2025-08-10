use lazy_static::lazy_static;
use tokio::task::coop::RestoreOnPending;
use std::{sync::Mutex};
use crate::module_bindings::DbConnection;
use cse_common::*;
use cse_common::cse_substate::CSESubstate;
use spacetimedb_sdk::credentials;
use spacetimedb_sdk::Error;
use spacetimedb_sdk::Identity;
use crate::module_bindings::ErrorContext;

fn creds_store() -> credentials::File
{
  return credentials::File::new(CREDS_SCRAPER);
}

/// Our `on_connect` callback: save our credentials to a file.
fn on_connected(_ctx: &DbConnection, _identity: Identity, token: &str) 
{
  if let Err(e) = creds_store().save(token) 
  {
    eprintln!("Failed to save credentials: {:?}", e);
  }
}

fn on_connect_error(_ctx: &ErrorContext, err: Error) 
{
  eprintln!("Connection error: {:?}", err);
  std::process::exit(1);
}

/// Our `on_disconnect` callback: print a note, then exit the process.
fn on_disconnected(_ctx: &ErrorContext, err: Option<Error>) 
{
  if let Some(err) = err 
  {
    eprintln!("Disconnected: {}", err);
    std::process::exit(1);
  } 
  else 
  {
    println!("Disconnected.");
    std::process::exit(0);
  }
}

fn connect_to_database() -> DbConnection
{
  DbConnection::builder()
    // Register our `on_connect` callback, which will save our auth token.
    .on_connect(on_connected)
    // Register our `on_connect_error` callback, which will print a message, then exit the process.
    .on_connect_error(on_connect_error)
    // Our `on_disconnect` callback, which will print a message, then exit the process.
    .on_disconnect(on_disconnected)
    // If the user has previously connected, we'll have saved a token in the `on_connect` callback.
    // In that case, we'll load it and pass it to `with_token`,
    // so we can re-authenticate as the same `Identity`.
    .with_token(creds_store().load().expect("Error loading credentials"))
    // Set the database name we chose when we called `spacetime publish`.
    .with_module_name(DATABASE_NAME)
    // Set the URI of the SpacetimeDB host that's running our database.
    .with_uri(URL_SERVER)
    // Finalize configuration and connect!
    .build()
    .expect("Failed to connect")
}

#[derive(Clone, Copy, PartialEq)]
pub enum ResourceScrapeState
{
  RetrievingFromDB,
  RetrievedFromDB,
  RetrievingFromEveServers,
  Valid,
}

#[derive(Clone)]
pub struct CSEScraperState 
{
  pub versions_state: CSESubstate<ResourceScrapeState>,
  pub regions_state: CSESubstate<ResourceScrapeState>,
  pub constellations_state: CSESubstate<ResourceScrapeState>,
  pub universe_version_valid: bool,
}

lazy_static! {
    pub static ref G_SCRAPER_STATE: Mutex<CSEScraperState> = Mutex::new(CSEScraperState {
        versions_state: CSESubstate::new(ResourceScrapeState::RetrievingFromDB),
        regions_state: CSESubstate::new(ResourceScrapeState::RetrievingFromDB),
        constellations_state: CSESubstate::new(ResourceScrapeState::RetrievingFromDB),
        universe_version_valid: false,
    });

    pub static ref G_DB_CONN: Mutex<DbConnection> = Mutex::new(connect_to_database());    
}