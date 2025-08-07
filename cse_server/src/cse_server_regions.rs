use spacetimedb::{table, Table, ReducerContext, SpacetimeType};

#[table(name = region, public)]
pub struct Region
{
  #[primary_key]
  region_id: i64,
  region_name: String,
  description: String,
}

#[spacetimedb::reducer]
pub fn add_region(ctx: &ReducerContext, region_id: i64, region_name: String, description: String) 
{
  let new_region = Region
  {
    region_id,
    region_name, 
    description,
  };
  let insert_result = ctx.db.region().try_insert(new_region);
  match insert_result
  {
    Ok(row) =>
    {
      log::info!("Added region {}", row.region_name);
    }
    
    Err(insert_result) =>
    {
      log::warn!("{}", insert_result);
    }
  }
}