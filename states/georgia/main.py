import random
import re
from bs4 import BeautifulSoup
from bs4.element import NavigableString

from common import cache_request, decode_email, diff_and_save

LIST_URL = "https://elections.sos.ga.gov/Elections/countyregistrars.do"
DETAIL_URL = "https://elections.sos.ga.gov/Elections/contactinfo.do"


def parse_addr_line(key, line):
  if not isinstance(line, NavigableString):
    return {}
  else:
    return {key: line.strip().title().replace(' Ga ', ' GA ')}

def parse_contact_line(line):
  if not isinstance(line, NavigableString):
    return {}
  parsed = line.split(':')
  if len(parsed) == 2:
    k, v = parsed
    return {k.strip(): v.strip()}
  return {}

def parse_contact(h4):
  title = h4.text
  line1 = h4.next_element.next_element
  line2 = line1.next_element.next_element
  if title.endswith('Address:'):
    return {
      'kind': title.split(':')[0],
      **parse_addr_line('addr1', line1),
      **parse_addr_line('addr2', line2),
    }
  elif title == 'Contact Information:':
    return {
      'kind': title.split(':')[0],
      **parse_contact_line(line1),
      **parse_contact_line(line2),
    }
  else:
    raise ValueError('Encountered unrecognized contact')

def parse_county(soup):
  soup = soup.find(id='Table1')
  registrar_str = soup.find('hr').next_element
  name = registrar_str.next_element.next_element
  county = re.search('(.* County) Chief Registrar', registrar_str).group(1).title()

  contact_els = soup.find_all('h4')
  contacts = [parse_contact(contact) for contact in contact_els]
  contacts_dict = {
    contact['kind']: contact
    for contact in contacts
  }

  email_el = soup.find('span', class_='__cf_email__')
  email = decode_email(email_el.get('data-cfemail')).strip() if email_el else None
  fax = contacts_dict.get('Contact Information', {}).get('Fax')

  return {
    'locale': county.strip(),
    'county': county.strip(),
    'official': name.title().strip(),
    'emails': [email] if email else [],
    'faxes': [fax] if fax else [],
    'contacts': contacts_dict,
  }


if __name__ == '__main__':
  data = []
  text = cache_request(LIST_URL)
  soup = BeautifulSoup(text, 'html.parser')
  for county in soup.find(id='idTown')('option'):
    wait = random.uniform(1, 3)
    text = cache_request(DETAIL_URL, method='POST', data={'idTown': county['value'], 'contactType': 'R'}, wait=wait)
    data.append(parse_county(BeautifulSoup(text, 'html.parser')))

  # sort by locale for consistent ordering
  data.sort(key=lambda x: x['locale'])
  diff_and_save(data, 'public/georgia.json')