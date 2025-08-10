use spacetimedb::{table, Table, ReducerContext};
use crate::cse_server_types::DbVector3F64;

#[table(name = constellations, public)]
pub struct Constellation
{
  #[primary_key]
  constellation_id: i64,
  name: String,
  position: DbVector3F64,
  region_id: i64
}

#[spacetimedb::reducer]
pub fn add_constellation(ctx: &ReducerContext, constellation: Constellation) 
{
  let insert_result = ctx.db.constellations().try_insert(constellation);
  match insert_result
  {
    Ok(row) =>
    {
      log::info!("Added constellation {}", row.name);
    }
    
    Err(insert_result) =>
    {
      log::warn!("{}", insert_result);
    }
  }
}