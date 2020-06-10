import re
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from common import cache_request

BASE_URL = 'https://elections.maryland.gov/about/county_boards.html'


def find_re(regex, lines, find_all=False):
  results = []
  for line in lines:
    if isinstance(line, NavigableString):
      match = regex.search(line)
      if match and not find_all:
        return match.group(1).strip()
      if match and find_all:
        results += [match.group(1).strip()]
  if find_all:
    return results
  return None


phone_re = re.compile(r'(\d{3}-\d{3}-\d{4})$')
fax_re = re.compile(r'(\d{3}-\d{3}-\d{4}) \(fax', re.IGNORECASE)
email_re = re.compile(r'[\w\-.]+@([\w\-]+\.)+[\w\-]{2,4}')
election_director_re = re.compile(r'(.*),\w+Election Director')


def find_hrefs(lines):
  results = {
    'emails': [],
    'urls': [],
  }
  for line in lines:
    if isinstance(line, Tag) and line.name == 'a':
      if line['href'].startswith('mailto:'):
        results['emails'] += [line['href'][7:].strip()]
      elif email_re.search(line.text):  # someone uses http://bob@gmail.com style email
        results['emails'] += [email_re.search(line.text).group(0).strip()]
      elif not line['href'].startswith('https://www.google.com/maps/dir/'):
        results['urls'] += [line['href']]
  return results


def fetch_data():
  text = cache_request(BASE_URL)
  soup = BeautifulSoup(text, 'lxml')
  counties = soup.select('div.mdgov_contentWrapper > p')

  # lines = [line for line in line_gen(counties[1].children)]
  data = []
  for county in counties:
    lines = list(county.children)
    href_datum = find_hrefs(lines)
    url_datum = {'url': href_datum['urls'][0]} if href_datum['urls'] else {}

    geo = lines[0].text.strip()
    if geo.endswith('City'):
      geo_datum = {
        'locale': geo + ':',
        'city': geo,
      }
    else:  # for Baltimore
      county = geo if geo.endswith(' County') else geo + ' County'
      geo_datum = {
        'locale': ':' + county,
        'county': county,
      }

    datum = {
      **geo_datum,
      'official': find_re(election_director_re, lines),
      'phones': find_re(phone_re, lines, find_all=True),
      'faxes': [find_re(fax_re, lines)],
      **url_datum,
      **href_datum,
    }

    assert datum['emails']
    assert find_re(fax_re, lines)
    data += [datum]

  return data


if __name__ == '__main__':
  print(fetch_data())
