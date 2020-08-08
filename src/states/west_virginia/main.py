import re
from bs4 import BeautifulSoup
from common import cache_request


BASE_URL = 'https://sos.wv.gov/elections/Pages/CountyClerkDirectory.aspx'

re_phone_fax = re.compile(r'(\d{3}\D*?\d{3}\D*?\d{4}(?:\D*?[xX]\D*?\d+)?)')


def parse_county(row):
  items = [td.text for td in row('td')]

  # some counties have an empty first element
  if not items[0].strip():
    items.pop(0)

  county = items[0] + ' County'
  return {
    'county': county,
    'locale': county,
    'clerk': items[1],
    'address': ', '.join(x.strip() for x in items[2].strip().split('\n')),
    'phones': re_phone_fax.findall(items[3]),
    'faxes': re_phone_fax.findall(items[4]),
    'emails': [items[5].strip()],
  }


def fetch_data(verbose=True):  # pylint: disable=unused-argument
  html = cache_request(BASE_URL)
  soup = BeautifulSoup(html, 'html.parser')
  return [parse_county(row) for row in soup.body.select('tbody tr')]


if __name__ == '__main__':
  print(fetch_data())
