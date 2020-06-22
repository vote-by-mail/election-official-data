import csv
import re
from io import StringIO
from bs4 import BeautifulSoup
from common import cache_request

BASE_URL = 'https://app.sos.nh.gov/Public/Reports.aspx'

re_email = re.compile(r'^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$')

def assert_list_match(x, y):
  assert(len(x) == len(y))
  for x_el, y_el in zip(x, y):
    assert(x_el == y_el)

def assert_match(x, y):
  assert(x['city'] == y['city'])
  assert(x['address'] == y['address'])
  assert(x['locale'] == y['locale'])
  assert_list_match(x['emails'], y['emails'])
  assert_list_match(x['phones'], y['phones'])
  assert_list_match(x['faxes'], y['faxes'])

def parse_csv(text):
  '''
  Each row represents a "Ward"; there may be multiple in each city
  This dedupes and asserts that the city entries are otherwise identical
  '''
  csv_str = StringIO(text)
  reader = csv.DictReader(csv_str, delimiter=',')
  raw_clerk_data = [extract_clerk_data(row) for row in reader]

  # dedupe -- only take first entry of each city
  clerk_dict = {}
  for datum in raw_clerk_data:
    if datum['city'] in clerk_dict:
      assert_match(datum, clerk_dict[datum['city']])
    else:
      clerk_dict[datum['city']] = datum
  return list(clerk_dict.values())


def extract_clerk_data(row):
  town_or_city = extract_city_without_ward(row)

  clerk_data_entry = {
    'city': town_or_city,
    'address': row['Address'].strip(),
    'locale': town_or_city,
    'emails': [row['E-Mail']] if re_email.match(row['E-Mail']) else [],
    'phones': ['603-' + row['Phone (area code 603)']] if row['Phone (area code 603)'] else [],
    'faxes': ['603-' + row['Fax']] if(row['Fax']) else [],
  }

  if row['Clerk']:
    clerk_data_entry['official'] = ' '.join(x.capitalize() for x in row['Clerk'].split())

  return clerk_data_entry


def extract_city_without_ward(row):
  capitalized_city = ' '.join(x.capitalize() for x in row['Town/City'].split())

  # removes everything after 'Ward' (no-op if 'Ward' isn't in string)
  return capitalized_city.split(' Ward ')[0].strip()

def fetch_data():
  # extract __viewstate and other form params for .aspx
  page = cache_request(BASE_URL)
  soup = BeautifulSoup(page, 'lxml')
  form = soup.find('form')
  form_data = {form_input['name']: form_input['value'] for form_input in form('input')}
  form_data['ctl00$MainContentPlaceHolder$PPReport'] = 'rdoCsv'

  csv_text = cache_request(BASE_URL, method='POST', data=form_data)
  return parse_csv(csv_text)


if __name__ == '__main__':
  print(fetch_data())
