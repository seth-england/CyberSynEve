use spacetimedb::{SpacetimeType};

#[derive(SpacetimeType, Clone, Debug)]
pub struct DbVector3F64 
{
    pub x: f64,
    pub y: f64,
    pub z: f64
}