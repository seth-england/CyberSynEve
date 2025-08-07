use reqwest::Error;
use std::pin::Pin;
use std::future::Future;

pub type AsyncGetFunction = fn() -> Pin<Box<dyn Future<Output = Result<String, Error>>>>;

pub async fn get_url_text(url: String) -> Result<String, Error> 
{
  let url_result = reqwest::get(&url).await;
  match url_result 
  {
    Ok(res) =>
    {
      let text = res.text().await?;
      return Ok(text);
    } 

    Err(e) =>
    {
      panic!("{}", e)
    }  
  }
}
