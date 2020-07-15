import re
from bs4 import BeautifulSoup
from common import cache_request, to_list

BASE_URL = 'https://vip.sos.nd.gov/CountyAuditors.aspx'

re_phfaxemail = re.compile(
  r'\s*(?P<phone>\(?\s*\d{3}\s*\)?\s*\d{3}-?\d{4})\s*(?:.*?)?\n'  # ignore extension
  + r'\s*(?P<fax>\(?\s*\d{3}\s*\)?\s*\d{3}-?\d{4})\s*\n'
  + r'\s*(?P<email>(?:[\w\-\.]+)@(?:[\w\-\.]+)\.(?:[a-zA-Z]{2,5}))\s*',
  re.MULTILINE
)


def parse_row(row):
  cols = [col.get_text('\n').strip() for col in row('td')]
  county = f"{cols[1]} County"
  phfaxemail = re_phfaxemail.match(cols[3]).groupdict()
  return {
    'locale': county,
    'county': county,
    'official': cols[2],
    'phones': to_list(phfaxemail.get('phone')),
    'faxes': to_list(phfaxemail.get('fax')),
    'emails': to_list(phfaxemail.get('email')),
    'address': cols[4],
  }


def fetch_data():
  html = cache_request(BASE_URL)
  soup = BeautifulSoup(html, 'html.parser')
  return [parse_row(row) for row in soup.select('table#ctl00_ContentPlaceHolder1_rgCountyAuditors_ctl00 tbody tr')]


if __name__ == '__main__':
  print(fetch_data())
