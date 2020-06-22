import re
from bs4 import BeautifulSoup
from common import cache_request, to_list

BASE_URL = 'https://app.sos.nh.gov/Public/Reports.aspx'

re_row = re.compile(r'\n\s*(?P<city>.*?)(?:\s*WARD.*?)?\s*,\s*(?P<official>.+?)?\s*,'
                    + r'\s*(?P<address>.+?)?\s*,\s*(?P<phone>[\d-]+)?\s*,\s*(?P<fax>[\d-]+)?\s*,'
                    + r'\s*(?P<email>(?:[\w\-\.]+)@(?:[\w\-\.]+)\.(?:[a-zA-Z]{2,5}))?\s*,\s*(?P<url>.+?)?\s*,',
                    re.MULTILINE)


def assert_list_match(x, y):
  assert len(x) == len(y)
  for x_el, y_el in zip(x, y):
    assert x_el == y_el


def assert_match(x, y):
  assert x['city'] == y['city']
  assert x['address'] == y['address']
  assert x['locale'] == y['locale']
  assert_list_match(x['emails'], y['emails'])
  assert_list_match(x['phones'], y['phones'])
  assert_list_match(x['faxes'], y['faxes'])

def parse_csv(csv_text):
  '''
  Each row represents a "Ward"; there may be multiple in each city
  This dedupes and asserts that the city entries are otherwise identical
  '''
  raw_clerk_data = [clean_row(row.groupdict()) for row in re_row.finditer(csv_text)]

  # dedupe -- only take first entry of each city
  # assert that all other values are the same
  clerk_dict = {}
  for datum in raw_clerk_data:
    if datum['city'] in clerk_dict:
      assert_match(datum, clerk_dict[datum['city']])
    else:
      clerk_dict[datum['city']] = datum
  return list(clerk_dict.values())


def clean_row(row):
  row['city'] = ' '.join(x.capitalize() for x in row['city'].split())  # title() doesn't work on Beans's
  row['official'] = row['official'].title() if row['official'] else None
  row['locale'] = row['city']
  row['emails'] = to_list(row.pop('email'))
  row['phones'] = ['603-' + num for num in to_list(row.pop('phone'))]
  row['faxes'] = ['603-' + num for num in to_list(row.pop('fax'))]
  return row


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
