export function BuildURL(base_url: string, params: Record<string, string | number | boolean | undefined>) : string
{
  const url = new URL(base_url)
  const search_params = new URLSearchParams(url.search);
  for (const [key, value] of Object.entries(params))
  {
    if (value != undefined && value != null)
    {
      search_params.append(key, String(value))
    }
  }
  
  url.search = search_params.toString()
  return url.toString()
}