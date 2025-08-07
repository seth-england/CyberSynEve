use spacetimedb::{table};

#[table(name = version, public)]
pub struct cse_server_version
{
  #[primary_key]
  version_name: String,
  version_value: String
}