from bs4 import BeautifulSoup

from common import cache_selenium, normalize_state, diff_and_save


# js obfuscation requires cache_request_selenium
BASE_URL = 'https://www.sec.state.ma.us/ele/eleclk/clkidx.htm'



def parse_html(html):
  soup = BeautifulSoup(html, 'html.parser')
  raw_clerk_data = [x.text for x in soup.select_one('div', {'id': 'content_third'}).find_all("p")]
  sanitized_clerk_data = []

  for stripped_data in raw_clerk_data:
    stripped_data = [x.lstrip().rstrip() for x in stripped_data.split('\n')]

    if(len(stripped_data) < 8):  # all clerks data blocks follow the same exact format
      continue

    sanitized_data = {
      'locale': stripped_data[0].capitalize(),
      'city': stripped_data[0].capitalize(),
      'address': " ".join(x.capitalize() for x in " ".join(stripped_data[1:4]).split()),
      'phones': [stripped_data[4].split()[1]],
      'faxes': [stripped_data[5].split()[1]],
      'emails': [stripped_data[6].split()[1]],
      'url': stripped_data[7].split()[1]
    }
    sanitized_clerk_data.append(sanitized_data)

  return sanitized_clerk_data
  
def crawl_and_parse():
  html = cache_selenium(BASE_URL)
  data = parse_html(html)
  data = normalize_state(data)
  diff_and_save(data, 'public/massachusetts.json')


if __name__ == "__main__":
  crawl_and_parse()
