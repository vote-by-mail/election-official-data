from io import BytesIO
from io import StringIO
import re
from urllib.parse import urljoin
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from bs4 import BeautifulSoup
from common import cache_request

BASE_URL = 'https://www.ok.gov/elections/About_Us/County_Election_Boards/'

# covers county edge case where next line starts with *
re_county_section = re.compile(r'(?<=COUNTY\n).*?(?=\n\n|\n\*)', flags=re.MULTILINE + re.DOTALL)
re_phone_fax_section = re.compile(r'(?<=PHONE\n).*?(?=\n\n)', flags=re.MULTILINE + re.DOTALL)
re_mailing_section = re.compile(r'(?<=MAILING ADDRESS\n).*?(?=\n\n)', flags=re.MULTILINE + re.DOTALL)
re_number_space = re.compile(r'[\d]+\s*')


# Oklahoma uses pdfminer since its pdf doesn't work with PyPDF2
def get_pdf_text(url):
  req = cache_request(url, is_binary=True)
  with BytesIO(req) as pdf_file:
    with StringIO() as output:
      manager = PDFResourceManager()
      converter = TextConverter(manager, output, laparams=LAParams())
      interpreter = PDFPageInterpreter(manager, converter)
      for page in PDFPage.get_pages(pdf_file, set()):
        interpreter.process_page(page)
      converter.close()
      text = output.getvalue()
  return text


def parse_pdf(pdf_url):
  text = get_pdf_text(pdf_url)
  counties = re_number_space.sub('', '\n'.join(re_county_section.findall(text))).split('\n')
  phones_faxes = '\n'.join(re_phone_fax_section.findall(text)).split('\n')
  mailing_addrs = '\n'.join(re_mailing_section.findall(text)).split('\n')

  data = {}
  for county, phone_fax, mailing_addr in zip(counties, phones_faxes, mailing_addrs):
    county_name = f'{county} County'
    phone, fax = phone_fax.split(' ')
    data[county] = {
      'county': county_name,
      'locale': county_name,
      'phones': [phone],
      'faxes': [fax],
      'address': mailing_addr,
    }
  return data


def parse_email_list(email_list_url):
  text = cache_request(email_list_url)
  soup = BeautifulSoup(text, 'html.parser')
  email_by_county = {}
  for row in soup.find('tbody')('tr'):
    county_name = row.find('td').text
    email_tag = row.find('a')
    if email_tag is not None:
      email_by_county[county_name] = email_tag.text
  return email_by_county


def fetch_data():
  html = cache_request(BASE_URL)
  soup = BeautifulSoup(html, 'html.parser')
  pdf_url = urljoin(BASE_URL, soup.find('a', text=re.compile('^List of County Election Boards'))['href'])
  email_list_url = urljoin(BASE_URL, soup.find('a', text=re.compile('^County Election Board Email Addresses'))['href'])

  pdf_data = parse_pdf(pdf_url)
  email_data = parse_email_list(email_list_url)
  assert len(pdf_data) == len(email_data)

  for county_name, email in email_data.items():
    pdf_data[county_name]['emails'] = [email]

  return list(pdf_data.values())


if __name__ == "__main__":
  print(fetch_data())
