import re
from bs4 import BeautifulSoup
from common import cache_request, decode_email

re_strip_lines = re.compile(r'\s*\n\s*')
re_recorder = re.compile(
  r'(?P<official>\S.*\S)\s*\n.*County Recorder\s*'
  r'(?:Physical:\s*(?P<physicalAddress>(.|\n)*?)\s*Mailing:\s*)?'
  r'(?:(?P<address>(.|\n)*?\d{5}(?:-\d+)?))',
  re.MULTILINE)
re_phone = re.compile(r'Phone\s*-?\s*(.*)\n')
re_fax = re.compile(r'Fax\s*-?\s*(.*)\n')


def parse_county(soup):
  county = soup.find('h2').text
  text = re_strip_lines.sub('\n', soup.get_text('\n'))

  # use County Recorder as the primary official since they handle voter registration
  datum = re_recorder.search(text).groupdict()
  if datum['physicalAddress'] is None:
    datum.pop('physicalAddress')

  return {
    **datum,
    'county': county,
    'locale': county,
    'url': soup.select('a[href^=http]')[0].get('href').strip(),
    'emails': [decode_email(x.get('data-cfemail')) for x in soup.find_all('span', class_='__cf_email__')],
    'phones': [ph for phones in re_phone.findall(text) for ph in phones.split(' or ')],
    'faxes': [fax for faxes in re_fax.findall(text) for fax in faxes.split(' or ')],
  }


def fetch_data():
  html = cache_request('https://azsos.gov/county-election-info')
  soup = BeautifulSoup(html, 'html.parser')
  return [parse_county(county) for county in soup('div', id=re.compile('^county_info_')) if county.find('h2')]


if __name__ == '__main__':
  print(fetch_data())
