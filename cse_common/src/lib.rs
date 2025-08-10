pub mod cse_math_types;
pub mod cse_substate;
use std::pin::Pin;
use std::future::Future;

pub type AsyncAnyFunction = fn() -> Pin<Box<dyn Future<Output = ()>>>;

macro_rules! eve_url 
{
    ($path:literal) => 
    {
      concat!("https://esi.evetech.net/dev/", $path)
    };
}

pub const URL_SERVER: &str = "http://127.0.0.1:3000";

pub const URL_EVE_REGIONS: &str = eve_url!("universe/regions/");
pub const URL_EVE_CONSTELLATIONS: &str = eve_url!("universe/constellations/");

pub const DATABASE_NAME: &str = "cse-server";

pub const SERVER_URL: &str = "TEST";

pub const CREDS_SCRAPER: &str = "creds_scraper";

pub const VERSION_NAME_EVE_UNIVERSE: &str = "VERSION_EVE_UNIVERSE";
pub const VERSION_EVE_UNIVERSE: &str = "1.0";

pub fn add(left: u64, right: u64) -> u64 {
    left + right
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn it_works() {
        let result = add(2, 2);
        assert_eq!(result, 4);
    }
}
