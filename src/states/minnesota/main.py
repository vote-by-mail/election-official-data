import re
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from common import cache_request

BASE_URL = 'https://www.sos.state.mn.us/elections-voting/find-county-election-office/'


def line_gen(siblings):
  text = ''
  for x in siblings:
    if isinstance(x, NavigableString):
      text += x.strip()
    elif isinstance(x, Tag) and x.name == 'br':
      yield text
      text = ''
    elif isinstance(x, Tag) and x.name == 'span':
      text += x.text.strip()
    elif isinstance(x, Tag) and x.name == 'h3':
      yield text
      return


def parse_county(county, datum):
  absentee_voting_contact = datum.find('h3', class_='contentpage-h3', text='Absentee voting contact')

  _iter = line_gen(absentee_voting_contact.next_siblings)

  name = next(_iter)
  phone = next(_iter)
  fax = next(_iter)
  email = next(_iter)
  return {
    'locale': county.text,
    'county': county.text,
    'official': name,
    'phones': [re.search(r'Phone: ([0-9\-]+)', phone).group(1)],
    'faxes': [re.search(r'Fax: ([0-9\-]+)', fax).group(1)],
    'emails': [re.search(r'Email:\s*(\S+)', email).group(1)],
  }


def fetch_data():
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
