from common import cache_request
import json
import re
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

def find_re(regex, lines, find_all=False):
  results = []
  for line in lines:
    if isinstance(line, NavigableString):
      match = regex.search(line)
      if match and not find_all:
        return match.group(1)
      if match and find_all:
        results += [match.group(1)]
  return results

phone_re = re.compile('(\d{3}-\d{3}-\d{4})$')
fax_re = re.compile('(\d{3}-\d{3}-\d{4}) \(Fax\)')
email_re = re.compile(r'[\w\-.]+@([\w\-]+\.)+[\w\-]{2,4}')
election_director_re = re.compile('(.*), Election Director')

def find_hrefs(line):
  results = {
    'emails': [],
    'urls': [],
  }
  for line in lines:
    if isinstance(line, Tag) and line.name == 'a':
      if line['href'].startswith('mailto:'):
        results['emails'] += [line['href'][7:]]
      if email_re.search(line.text):  # someone uses http://bob@gmail.com style email
        results['emails'] += [email_re.search(line.text).group(0)]
      elif not line['href'].startswith('https://www.google.com/maps/dir/'):
        results['urls'] += [line['href']]
  return results

if __name__ == '__main__':
  text = cache_request('https://elections.maryland.gov/about/county_boards.html')
  soup = BeautifulSoup(text, 'lxml')
  counties = soup.select('div.mdgov_contentWrapper > p')

  # lines = [line for line in line_gen(counties[1].children)]
  data = []
  for county in counties:
    lines = [l for l in county.children]
    datum = {
      'county': lines[0].text,
      'name': find_re(election_director_re, lines),
      'phone': find_re(phone_re, lines, find_all=True),
      'fax': find_re(fax_re, lines),
      **find_hrefs(lines)
    }
    assert(datum['emails'])
    data += [datum]

  with open('public/maryland.json', 'w') as fh:
    json.dump(data, fh)
