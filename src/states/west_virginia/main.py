from bs4 import BeautifulSoup
from common import cache_request


BASE_URL = 'https://sos.wv.gov/elections/Pages/CountyClerkDirectory.aspx'


def fetch_data():
  text = cache_request(BASE_URL)
  soup = BeautifulSoup(text, 'html.parser')

  raw_rows = soup.body.find_all('tr')

  counties = []
  for table_row in raw_rows:
    if table_row is None:
      continue
    county = {}

    items = table_row.find_all('td')

    # Some counties' data is offset one index forward.
    starting_index = 0
    if len(items) < 6:
      continue
    if len(items) == 6:
      starting_index = 0
    else:
      starting_index = 1

    county['county'] = items[starting_index].text + ' County'
    county['locale'] = county['county']
    county['clerk'] = items[starting_index + 1].text
    county['address'] = items[starting_index + 2].text.replace('\n', ' ').strip(' ')
    # [:12] removes extension
    county['phones'] = [items[starting_index + 3].text.replace('(', '').replace(')', '-').replace(' ', '')[:12]]
    county['faxes'] = [items[starting_index + 4].text.replace('(', '').replace(')', '-').replace(' ', '')]
    county['emails'] = [items[starting_index + 5].text.replace(' ', '')]
    counties.append(county)

  return counties


if __name__ == '__main__':
  print(fetch_data())
