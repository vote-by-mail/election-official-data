from bs4 import BeautifulSoup
from common import cache_request


def main():
  # Key is county name, value is email address.
  email_by_county = {}

  text = cache_request('https://www.ok.gov/elections/County_Election_Board_Email_Addresses.html')
  soup = BeautifulSoup(text, 'html.parser')

  table = soup.find('table')
  table_body = table.find('tbody')

  rows = table_body.find_all('tr')
  for row in rows:
    county_name = row.find('td').string
    
    # Can't get string without check because it may be None.
    email_tag = row.find('a')
    if email_tag is not None:
      email_by_county[county_name] = email_tag.string

  return email_by_county

if __name__ == '__main__':
  main()