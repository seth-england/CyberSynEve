use cse_http_helpers;
use cse_common::cse_math_types::{self, CSEVec3F64};
use cse_common::{cse_substate::CSESubstateTrait};
use serde::{Serialize, Deserialize};
use crate::module_bindings::{add_constellation, Constellation, DbVector3F64};
use crate::{cse_scraper_state::{ResourceScrapeState, G_DB_CONN, G_SCRAPER_STATE}, module_bindings::add_region};

#[derive(Serialize, Deserialize, Debug)]
pub struct EveConstellation
{
  constellation_id: i64,
  name: String,
  position: CSEVec3F64,
  region_id: i64
}

async fn get_constellations_helper(constellation_ids: Vec<i64>)
{
  // Set up the futures for fetching the urls
  let mut url_futures = Vec::new();
  for region_id in constellation_ids.iter()
  {
    let mut url =  String::from(cse_common::URL_EVE_CONSTELLATIONS);
    url.push_str(region_id.to_string().as_str());
    url.push('/');

    let fetch_future = cse_http_helpers::get_url_text(url);
    url_futures.push(fetch_future);
  }
  
  let url_futures_results = futures::future::join_all(url_futures).await;
  let mut all_constellations = Vec::new();
  for url_futures_result in url_futures_results.iter()
  {
    match url_futures_result  
    {
      Ok(constellation) =>
      {
        let region_result = serde_json::from_str::<EveConstellation>(constellation.as_str());
        match region_result
        {
          Ok(region) =>
          {
            all_constellations.push(region);
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

  for constellation in all_constellations.iter()
  {
    let db_constellation = Constellation
    {
      constellation_id: constellation.constellation_id,
      name: constellation.name.clone(),
      position: DbVector3F64 { x: constellation.position.x, y: constellation.position.y, z: constellation.position.z },
      region_id: constellation.region_id
    };
    let db_res = G_DB_CONN.lock().unwrap().reducers.add_constellation(db_constellation);
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
  println!("Fetched constellations from eve servers {}{}", file!(), line!());
}

pub async fn get_constellations()
{
  println!("Fetching constellations from eve servers {}{}", file!(), line!());
  let fetch_result = cse_http_helpers::get_url_text(cse_common::URL_EVE_CONSTELLATIONS.to_string()).await;
  match fetch_result
  {
    Ok(constellation_ids_string) =>
    {
      let constellation_ids_result: Result<Vec<i64>, serde_json::Error> = serde_json::from_str(constellation_ids_string.as_str());
      match constellation_ids_result
      {
        Ok(region_ids) =>
        {
          get_constellations_helper(region_ids).await;
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