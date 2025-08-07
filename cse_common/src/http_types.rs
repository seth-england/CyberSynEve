
use serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize, Debug)]
pub struct EVERegion
{
  pub region_id: i64,
  pub name: String,
  pub description: Option<String>,
  pub constellations: Vec<i64>
}