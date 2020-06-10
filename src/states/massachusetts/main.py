import re
from bs4 import BeautifulSoup
from common import cache_selenium

# js obfuscation requires cache_request_selenium
BASE_URL = 'https://www.sec.state.ma.us/ele/eleclk/clkidx.htm'

re_city = re.compile(r'^(.*?)\n')
re_addr = re.compile(r'\n(.*?)\n\s*Phone', flags=re.MULTILINE + re.DOTALL)
re_phone = re.compile(r'\n\s*Phone:\s*(.*?)\n')
re_fax = re.compile(r'\n\s*Fax:\s*(.*?)\n')
re_email = re.compile(r'\n\s*Email:\s*(.*?)\n')
re_url = re.compile(r'\n\s*Website:\s*(.*?)\n')


def parse_html(html):
  soup = BeautifulSoup(html, 'html.parser')
  raw_clerk_data = [x.text.strip() for x in soup.select_one("div", id="content_third")("p")]
  data = []

  for stripped_data in raw_clerk_data:
    city = (re_city.findall(stripped_data) or [''])[0].title()
    if not city:
      continue
    data.append({
      'locale': city,
      'city': city,
      'address': ', '.join(x.strip().title() for x in re_addr.findall(stripped_data)[0].split('\n')),
      'phones': re_phone.findall(stripped_data),
      'faxes': re_fax.findall(stripped_data),
      'emails': re_email.findall(stripped_data),
      'url': (re_email.findall(stripped_data) or [None])[0],
    })

  return data


def fetch_data():
  html = cache_selenium(BASE_URL)
  data = parse_html(html)
  return data


if __name__ == "__main__":
  print(fetch_data())
