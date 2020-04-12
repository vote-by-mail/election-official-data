import PyPDF2
import re

city_start_re = re.compile('^(CITY|TOWN|VILLAGE) OF')
end_page_re = re.compile('^Page \d+ of 360$')

def chunk_city(text):
  lines = text.split('\n')

  city_lines = []
  within_city = False

  for line in lines:
    if city_start_re.search(line):
      within_city = True
      if city_lines:
        yield '\n'.join(city_lines)
        city_lines = []

    elif end_page_re.search(line):
      if city_lines:
        yield '\n'.join(city_lines)
        return

    if within_city:
      city_lines += [line]

city_county_re = re.compile(r'(CITY|TOWN|VILLAGE)\s+OF\s+([A-Z \n]+)\s+-\s+([A-Z \n]+)\s+COUNTY')
clerk_re = re.compile('CLERK: (.*)')
# address_re = re.compile(r'Municipal Address :([A-Z0-9, \n]+\s+\d{5}(-\d{4})?)')
municipal_address_re = re.compile(r'Municipal Address :([^:]+\n)+')
mailing_address_re = re.compile(r'Mailing Address :([^:]+\n)+')
phone_re = re.compile(r'Phone \d: ([()\d-]+)')
fax_re = re.compile(r'Fax: ([()\d-]+)')

def parse_city_lines(lines):
  match = city_county_re.search(lines)
  clerk = clerk_re.search(lines).group(1)
  municipal_address = municipal_address_re.search(lines)
  mailing_address = mailing_address_re.search(lines)
  phones = phone_re.findall(lines)
  fax = fax_re.search(lines)
  return {
    'type': match.group(1),
    'city': match.group(2),
    'county': match.group(3),
    'clerk': clerk,
    'municipal_address': municipal_address.group(1) if municipal_address else None,
    'mailing_address': mailing_address.group(1) if mailing_address else None,
    'phones': phones,
    'fax': fax.group(1) if fax else None,
  }

with open('results/WI Municipal Clerks no emails Updated 3-23-2020.pdf', 'rb') as fh:
  pdf_reader = PyPDF2.PdfFileReader(fh)
  # full_text = [pdf_reader.getPage(page).extractText() for page in range(pdf_reader.numPages)]
  text = pdf_reader.getPage(3).extractText()
  for city_lines in chunk_city(text):
    # print(city_lines)
    print(parse_city_lines(city_lines))

