from bs4 import BeautifulSoup
from common import cache_request


def fetch_data():
  text = cache_request('https://www.sos.ks.gov/elections/county_election_officers_all.aspx')
  soup = BeautifulSoup(text, 'html.parser')

  # Remove first labels row.
  raw_rows = soup.body.find_all('tr')[1:]

  counties = []
  for table_rows in raw_rows:
    county = {}

    items = table_rows.find_all('font')

    county['county'] = items[0].text + ' County'
    county['locale'] = county['county']
    county['officer'] = items[1].text
    county['emails'] = [items[2].text]
    # Index 3 is hours of operation, which we don't care about.
    county['phones'] = [items[4].text.replace('\n', '').replace('(', '').replace(')', '-')]
    county['faxes'] = [items[5].text.replace('\n', '').replace('(', '').replace(')', '-')]
    # Only some counties have a second address line.
    address_line2 = items[7].text
    if len(address_line2) > 1:
      address_line2 = ' ' + address_line2 + ' '
    address = (items[6].text
               + address_line2
               + items[8].text
               + ' '
               + items[9].text
               + items[10].text)
    county['address'] = address.replace('\n', ' ').replace('\xa0', ' ')[:-1]

    counties.append(county)

  return counties


if __name__ == '__main__':
  print(fetch_data())
