import re
from bs4 import BeautifulSoup
from common import cache_request

BASE_URL = 'https://www.sos.state.mn.us/elections-voting/find-county-election-office/'

re_lines = re.compile(r'(?<=Absentee voting contact)\s*(.*?)\s*'
                      + r'Phone:\s*([0-9\-]+)(?:\s*ext\s*\d+)?\s*Fax:\s*([0-9\-]+)\s*Email:\s*(\S+)',
                      re.DOTALL)


def parse_county(county, datum):
  lines = re_lines.findall(datum.get_text('\n'))[0]
  return {
    'locale': county.text,
    'county': county.text,
    'official': lines[0],
    'phones': [lines[1]],
    'faxes': [lines[2]],
    'emails': [lines[3]],
  }


def fetch_data(verbose=True):  # pylint: disable=unused-argument
  text = cache_request(BASE_URL)
  soup = BeautifulSoup(text, 'lxml')
  counties = soup.select('h2.contentpage-h2 a')

  data = []
  for county in counties:
    data_id = county['data-target'].split('#')[1]
    datum = soup.find(id=data_id)
    data.append(parse_county(county, datum))

  return data


if __name__ == '__main__':
  print(fetch_data())
