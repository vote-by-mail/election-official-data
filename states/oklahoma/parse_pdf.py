from common import cache_request
from io import BytesIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
import re


PDF_URL = 'https://www.ok.gov/elections/documents/CEB_Physical%20Addresses_%283-19-2020%29.pdf'

# covers county edge case where next line starts with *
re_county_section = re.compile(r'(?<=COUNTY\n).*?(?=\n\n|\n\*)', flags=re.MULTILINE + re.DOTALL)
re_phone_fax_section = re.compile(r'(?<=PHONE\n).*?(?=\n\n)', flags=re.MULTILINE + re.DOTALL)
re_mailing_section = re.compile(r'(?<=MAILING ADDRESS\n).*?(?=\n\n)', flags=re.MULTILINE + re.DOTALL)
re_number_space = re.compile(r'[\d]+\s*')


def get_pdf_text(url):
  req = cache_request(url, is_binary=True)
  with BytesIO(req) as fh:
    with StringIO() as output:
      manager = PDFResourceManager()
      converter = TextConverter(manager, output, laparams=LAParams())
      interpreter = PDFPageInterpreter(manager, converter)
      for page in PDFPage.get_pages(fh, set()):
        interpreter.process_page(page)
      converter.close()
      text = output.getvalue()
  return text


def parse_pdf():
  text = get_pdf_text(PDF_URL)

  counties = re_number_space.sub('', '\n'.join(re_county_section.findall(text))).split('\n')
  phones_faxes = '\n'.join(re_phone_fax_section.findall(text)).split('\n')
  mailing_addrs = '\n'.join(re_mailing_section.findall(text)).split('\n')
  assert(len(counties) == len(phones_faxes))
  assert(len(counties) == len(mailing_addrs))

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
