from common import cache_request, to_list, diff_and_save
import re
from bs4 import BeautifulSoup


re_extra_spaces = re.compile(r'[^\S\n]+')
re_locale_address = re.compile(r'(?P<locale>\S([^\S\n]|\w)*\s*County)\s*Board of Elections\s*(?P<address>\S.*\d{5}(-\d+)?)\s*', flags=re.MULTILINE+re.DOTALL)
re_phone_line = re.compile(r'Phone:\s*(.*)\n')
re_fax_line = re.compile(r'Fax:\s*(.*)\n')
re_phone = re.compile(r'1?\D*\d{3}\D*\d{3}\D*\d{4}')

def parse_county(soup):
  # content is within the only table on the page, in 2 th cells
  blocks = soup.find_all('th')
  text1 = re_extra_spaces.sub(' ', blocks[0].get_text('\n'))

  # locale/county/address
  match = re_locale_address.search(text1)
  results = match.groupdict()
  results['county'] = results['locale']

  # phone/fax numbers
  results['phones'] = []
  for phone_line in re_phone_line.findall(text1):
    results['phones'] += re_phone.findall(phone_line)
  results['faxes'] = []
  for fax_line in re_fax_line.findall(text1):
    results['faxes'] += re_phone.findall(fax_line)

  # emails
  results['emails'] = sorted(set(i.get('href').replace('mailto:','').strip() for i in blocks[0].select('a[href^=mailto]')))
  results['emails'] = list(filter(lambda x: not x.startswith('http'), results['emails'])) # Erie county apparently only uses a web form

  # county elections url
  url = blocks[0].find('a', text=lambda x: x and x.startswith('Visit')).get('href')
  if url:
    results['url'] = url.strip()

  # officials
  officers = re_extra_spaces.sub(' ', blocks[1].get_text('\n')).split('\n')[1:]
  officers = [officer.split(',')[0] for officer in officers]
  results['official'] = officers[0]
  results['other_officials'] = officers[1:]

  for k in ['locale','emails','faxes','phones','county']:
    if results['locale'].startswith('Erie') and k == 'emails': #Erie County apparently only uses a web form
      continue
    assert(results[k])

  return results

if __name__ == '__main__':
  data = []
  text = cache_request('https://www.elections.ny.gov/CountyBoards.html')
  soup = BeautifulSoup(text, 'html.parser')

  for county_area in soup.find_all('area'):
    county_link = county_area['href']
    text = cache_request(county_link)
    data.append(parse_county(BeautifulSoup(text, 'html.parser')))

  # sort by locale for consistent ordering
  data.sort(key=lambda x: x['locale'])
  diff_and_save(data, 'public/new_york.json')
