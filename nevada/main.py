from common import cache_request
import json
import os
import re
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag


def is_element(el, tag):
  return isinstance(el, Tag) and el.name == tag

class ElemIterator():
  def __init__(self, els):
    self.els = els
    self.i = 0

  def peek(self):
    try:
      return self.els[self.i]
    except IndexError:
      return None

  def next(self):
    self.i += 1
    return self.els[self.i - 1]

  def hasNext(self):
    return len(self.els) > (self.i)

  def peek_till(self, tag):
    while not is_element(self.peek(), tag):
      self.next()

  def next_till(self, tag):
    self.peek_till(tag)
    self.next()


def parse_lines(iter_):
  iter_.peek_till('strong')

  county = []
  while iter_.hasNext():
    county += [iter_.next()]

    if is_element(iter_.peek(), 'strong'):
      yield ElemIterator(county)
      county = []

  yield ElemIterator(county)
  county = []


def parse_emails_url(iter_):
  emails = []
  url = None

  try:
    while True:
      iter_.peek_till('a')
      email = iter_.next()
      href = email['href']
      if href.startswith('mailto:'):
        if href[7:]:
          emails += [href[7:]]
        else:
          emails += [email.text]
      else:
        url = href
  except IndexError:
    pass
  return emails, url

def parse_url(iter_):
  iter_.peek_till('a')
  link = iter_.next()
  href = link['href']
  assert(not href.startswith('mailto:'))
  return [href]


def parse_county(iter_):
  county_title = iter_.next().text.strip().title()
  locale = re.match('(.*) (City|County)', county_title).group(0)

  if county_title.startswith('Clark County Elections Mailing Address'):
    emails, url = parse_emails_url(iter_)
    return {
      'locale': locale,
      'county': locale,
      'emails': emails,
    }

  while True:
    el = iter_.next()
    if isinstance(el, NavigableString):
      if 'Clerk' in el or 'Registrar' in el:
        official = el.strip().split(',')[0]
        break

  address = []
  while True:
    el = iter_.next()
    if isinstance(el, NavigableString):
      address += [el.strip()]
      if re.search(r'Nevada \d{5}', el) or re.search(r'NV \d{5}', el):
        break

  iter_.next_till('br')
  numbers = iter_.next().strip()

  emails, url  = parse_emails_url(iter_)

  init = { 'city': locale } if locale.endswith('City') else { 'county': locale }

  return {
    **init,
    'locale': locale,
    'official': official,
    'address': ', '.join(address),
    'emails': emails,
    'url': url,
  }

if __name__ == '__main__':
  # Actually this file: https://www.nvsos.gov/sos/elections/voters/county-clerk-contact-information
  # But it's behind a javascript test
  dir_path = os.path.dirname(os.path.realpath(__file__))
  with open(dir_path + '/cache/Nevada.htm') as fh:
    page = fh.read()
  soup = BeautifulSoup(page, 'lxml')
  ps = soup.select('div.content_area > p')
  iter_ = ElemIterator([x for p in ps for x in p.children])
  raw_counties = [parse_county(county) for county in parse_lines(iter_)]

  merge_counties = {}
  for county in raw_counties:
    locale = county['locale']
    if locale in merge_counties:
      merge_counties[locale]['emails'] += county['emails']
    else:
      merge_counties[locale] = county

  counties = list(merge_counties.values())
  assert(len(counties) == len(raw_counties) - 1)

  with open('public/nevada.json', 'w') as fh:
    json.dump(counties, fh)
