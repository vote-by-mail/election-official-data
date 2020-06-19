import re
import json
from common import cache_request, to_list

BASE_URL = "https://vt.ncsbe.gov/BOEInfo/"

# county data is already stored in a js variable on the page
re_counties = re.compile(r" var countyData = \((.*)\).filter")


def join_fields(datum, sep, keys):
  return sep.join(datum[key] for key in keys if datum[key])


def parse_county(county):
  county_name = county['Name'].title() + ' County'
  return {
    'locale': county_name,
    'county': county_name,
    'official': county['DirectorName'].title(),
    'emails': [county['Email']],
    'faxes': to_list(county['FaxNum']),
    'phones': [join_fields(county, ' x', ['OfficePhoneNum', 'OfficePhoneNumExt'])],
    'address': join_fields(county, ', ', ['MailingAddr1', 'MailingAddr2', 'MailingAddrCSZ']),
    'physicalAddress': join_fields(county, ', ', ['PhysicalAddr1', 'PhysicalAddr2', 'PhysicalAddrCSZ']),
    'url': county['WebsiteAddr'],
  }


def fetch_data():
  html = cache_request(BASE_URL)
  counties = json.loads(re_counties.findall(html)[0])
  return [parse_county(county) for county in counties]


if __name__ == '__main__':
  print(fetch_data())
