from bs4 import BeautifulSoup

from common import cache_request, normalize_state, diff_and_save
from parse_pdf import parse_pdf


EMAIL_LIST_URL = 'https://www.ok.gov/elections/County_Election_Board_Email_Addresses.html'

def parse_email_list():
  text = cache_request(EMAIL_LIST_URL)
  soup = BeautifulSoup(text, 'html.parser')
  email_by_county = {}
  for row in soup.find('tbody')('tr'):
    county_name = row.find('td').text
    email_tag = row.find('a')
    if email_tag is not None:
      email_by_county[county_name] = email_tag.text
  return email_by_county

def crawl_and_parse():
  pdf_data = parse_pdf()
  email_data = parse_email_list()
  assert(len(pdf_data) == len(email_data))

  for county_name, email in email_data.items():
    pdf_data[county_name]['emails'] = [email]

  data = normalize_state(list(pdf_data.values()))
  diff_and_save(data, 'public/oklahoma.json')

if __name__ == "__main__":
  crawl_and_parse()
