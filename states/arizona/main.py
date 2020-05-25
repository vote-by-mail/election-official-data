from common import cache_request, decode_email
import json
import re
from bs4 import BeautifulSoup
from functools import reduce

re_extra_spaces = re.compile(r'[^\S\n]+')
re_recorder = re.compile(r'(?P<recorder>\S.*\S)\s*\n.*County Recorder\s*Physical:\s*(?P<physical>\S.*\S)\s*Mailing:\s*(?P<mailing>\S.*\S)\s*(?P<city_state_zip>\S.*\d{5}(-\d+)?)', flags=re.MULTILINE)
re_recorder2 = re.compile(r'(?P<recorder>\S.*\S)\s*\n.*County Recorder\s*(?P<full_address>\S(.|\n)*?\d{5}(-\d+)?)\s', flags=re.MULTILINE)
re_director = re.compile(r'(?P<director>\S.*\S)\s*\n.*County\s*\w*\s*Director.*\n\s*Physical:\s*(?P<physical>\S.*\S)\s*Mailing:\s*(?P<mailing>\S.*\S)\s*(?P<city_state_zip>\S.*\d{5}(-\d+)?)\s', flags=re.MULTILINE)
re_director2 = re.compile(r'(?P<director>\S.*\S)\s*\n.*County\s*\w*\s*Director.*\n\s*(?P<full_address>\S*(.|\n)*?\d{5}(-\d+)?)\s', flags=re.MULTILINE)
re_phone_line = re_phone = re.compile(r'Phone\s*-?\s*(.*)\n')
re_fax_line = re.compile(r'Fax\s*-?\s*(1?\D*\d{3}\D*\d{3}\D*\d{4})\D*\n')
re_phone = re.compile(r'(\d{3}\D*\d{3}\D*\d{4})')

def parse_county(soup):
  results = {}
  results['county'] = soup.find('h2').text
  results['locale'] = results['county']

  text = re_extra_spaces.sub(' ', soup.get_text('\n')).replace('\n\n','\n')
  phone_lines = re_phone_line.findall(text)
  results['phones'] = sorted(set(re_phone.findall(' '.join(phone_lines))))
  fax_lines = re_fax_line.findall(text)
  results['faxes'] = sorted(set(re_phone.findall(' '.join(fax_lines))))

  results['url'] = soup.select('a[href^=http]')[0].get('href').strip()
  emails = [decode_email(x.get('data-cfemail')) for x in soup.find_all('span', class_='__cf_email__')]
  results['emails'] = sorted(set(emails))

  # use County Recorder as the primary official since they handle voter registration
  recorder = (re_recorder.search(text) or re_recorder2.search(text)).groupdict()
  results['official'] = recorder['recorder']
  results['officialTitle'] = 'County Recorder'
  results['address'] = recorder['full_address'] if recorder.get('full_address') else recorder['mailing'] + '\n' + recorder['city_state_zip']
  results['physicalAddress'] = recorder['full_address'] if recorder.get('full_address') else recorder['physical'] + '\n' + recorder['city_state_zip']

  # save info for County Elections Director as well
  director = (re_director.search(text) or re_director2.search(text)).groupdict()
  results['other_officials'] = [{'name': director['director'],
                                'title': 'County Elections Director',
                                'address': director['full_address'] if director.get('full_address') else director['mailing'] + '\n' + director['city_state_zip'],
                                'physicalAddress': director['full_address'] if director.get('full_address') else director['physical'] + '\n' + director['city_state_zip']
                                }]

  for k in ['locale','emails','faxes','phones','county']:
    if not results[k]:
      print(results['locale'],k)
    assert(results[k])

  return results

if __name__ == '__main__':
  data = []
  text = cache_request('https://azsos.gov/county-election-info')
  soup = BeautifulSoup(text, 'html.parser')
  for county in soup('div', id=re.compile('^county_info_')):
    if county.find('h2'): #there are extra blank divs
      data.append(parse_county(county))

  with open('public/arizona.json', 'w') as f:
    json.dump(data, f)
