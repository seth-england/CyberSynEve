use serde::{Serialize, Deserialize};
#[derive(Serialize, Deserialize, Debug)]
pub struct CSEVec3F64
{
  pub x: f64,
  pub y: f64,
  pub z: f64,
}