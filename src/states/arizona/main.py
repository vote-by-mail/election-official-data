import re
from bs4 import BeautifulSoup
from common import cache_request, decode_email

re_recorder_str = r'(?P<recorder>\S.*\S)\s*\n.*County Recorder\s*Physical:\s*(?P<physical>\S.*\S)\s*'
re_recorder_str += r'Mailing:\s*(?P<mailing>\S.*\S)\s*(?P<city_state_zip>\S.*\d{5}(-\d+)?)'
re_recorder = re.compile(re_recorder_str, flags=re.MULTILINE)

re_director_str = r'(?P<director>\S.*\S)\s*\n.*County\s*\w*\s*Director.*\n\s*Physical:\s*(?P<physical>\S.*\S)\s*'
re_director_str += r'Mailing:\s*(?P<mailing>\S.*\S)\s*(?P<city_state_zip>\S.*\d{5}(-\d+)?)\s'
re_director = re.compile(re_director_str, flags=re.MULTILINE)

re_director2_str = r'(?P<director>\S.*\S)\s*\n.*County\s*\w*\s*Director.*\n\s*'
re_director2_str += r'(?P<full_address>\S*(.|\n)*?\d{5}(-\d+)?)\s'
re_director2 = re.compile(re_director2_str, flags=re.MULTILINE)

re_extra_spaces = re.compile(r'[^\S\n]+')
re_recorder2 = re.compile(r'(?P<recorder>\S.*\S)\s*\n.*County Recorder\s*(?P<full_address>\S(.|\n)*?\d{5}(-\d+)?)\s',
                          flags=re.MULTILINE)
re_phone_line = re_phone = re.compile(r'Phone\s*-?\s*(.*)\n')
re_fax_line = re.compile(r'Fax\s*-?\s*(1?\D*\d{3}\D*\d{3}\D*\d{4})\D*\n')
re_phone = re.compile(r'(\d{3}\D*\d{3}\D*\d{4})')


def parse_county(soup):
  results = {}
  results['county'] = soup.find('h2').text
  results['locale'] = results['county']

  text = re_extra_spaces.sub(' ', soup.get_text('\n')).replace('\n\n', '\n')
  phone_lines = re_phone_line.findall(text)
  results['phones'] = re_phone.findall(' '.join(phone_lines))
  fax_lines = re_fax_line.findall(text)
  results['faxes'] = re_phone.findall(' '.join(fax_lines))

  results['url'] = soup.select('a[href^=http]')[0].get('href').strip()
  results['emails'] = [decode_email(x.get('data-cfemail')) for x in soup.find_all('span', class_='__cf_email__')]

  # use County Recorder as the primary official since they handle voter registration
  recorder = (re_recorder.search(text) or re_recorder2.search(text)).groupdict()
  results['official'] = recorder['recorder']
  results['officialTitle'] = 'County Recorder'
  if recorder.get('full_address'):
    results['address'] = recorder['full_address']
    results['physicalAddress'] = recorder['full_address']
  else:
    results['address'] = recorder['mailing'] + '\n' + recorder['city_state_zip']
    results['physicalAddress'] = recorder['physical'] + '\n' + recorder['city_state_zip']

  # save info for County Elections Director as well
  director = (re_director.search(text) or re_director2.search(text)).groupdict()
  if director.get('full_address'):
    director_address = director['full_address']
    director_physical_address = director['full_address']
  else:
    director_address = director['mailing'] + '\n' + director['city_state_zip']
    director_physical_address = director['physical'] + '\n' + director['city_state_zip']
  results['other_officials'] = [{
    'name': director['director'],
    'title': 'County Elections Director',
    'address': director_address,
    'physicalAddress': director_physical_address,
  }]

  for k in ['locale', 'emails', 'faxes', 'phones', 'county']:
    if not results[k]:
      print(results['locale'], k)
    assert results[k]

  return results


def fetch_data():
  data = []
  text = cache_request('https://azsos.gov/county-election-info')
  soup = BeautifulSoup(text, 'html.parser')
  for county in soup('div', id=re.compile('^county_info_')):
    if county.find('h2'):  # there are extra blank divs
      data.append(parse_county(county))

  return data


if __name__ == '__main__':
  print(fetch_data())
