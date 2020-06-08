import re
import json
import PyPDF2
from tqdm import tqdm


from common import dir_path

city_start_re = re.compile(r'^(CITY|TOWN|VILLAGE) OF')
end_page_re = re.compile(r'^Page \d+ of 360$')


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


city_county_re = re.compile(r'(CITY|TOWN|VILLAGE)\s+OF\s+([A-Z.\- \n]+)\s+-\s+([A-Z.\- \n]+\s+COUNTY|MULTIPLE\s+COUNTIES)')
clerk_re = re.compile(r'CLERK: (.*)')
deputy_clerk_re = re.compile('DEPUTY CLERK: (.*)')
# address_re = re.compile(r'Municipal Address :([A-Z0-9, \n]+\s+\d{5}(-\d{4})?)')
municipal_address_re = re.compile(r'Municipal Address :([^:]+\n)+')
mailing_address_re = re.compile(r'Mailing Address :([^:]+\n)+')
phone_re = re.compile(r'Phone \d: ([()\d-]+)')
fax_re = re.compile(r'Fax: ([()\d-]+)')
url_re = re.compile(r'(https?://[^\s/$.?#].[^\s]*)')


def first_group(regex, lines):
  match = regex.search(lines)
  return match.group(1).strip() if match else None


def strip_newline(string):
  return string.replace('\n', '')


def parse_city_lines(lines):
  match = city_county_re.search(lines)

  ret = {
    'key': strip_newline(match.group(0)).strip(),
    'city_type': match.group(1),
    'city': match.group(2),
    'county': match.group(3),
    'clerk': first_group(clerk_re, lines),
    'deputy_clerk': first_group(deputy_clerk_re, lines),
    'municipal_address': first_group(municipal_address_re, lines),
    'mailing_address': first_group(mailing_address_re, lines),
    'phones': phone_re.findall(lines),
    'fax': first_group(fax_re, lines),
    'url': first_group(url_re, lines),
  }

  return {k: strip_newline(v) if isinstance(v, str) else v for k, v in ret.items()}


def parse_pdf():
  with open(dir_path(__file__) + '/results/WI Municipal Clerks no emails Updated 3-23-2020.pdf', 'rb') as fh:
    pdf_reader = PyPDF2.PdfFileReader(fh)
    # full_text = [pdf_reader.getPage(page).extractText() for page in range(pdf_reader.numPages)]
    records = []
    for page_num in tqdm(range(pdf_reader.numPages)):
      text = pdf_reader.getPage(page_num).extractText()
      for city_lines in chunk_city(text):
        records += [parse_city_lines(city_lines)]

  with open(dir_path(__file__) + '/results/records.noemail.json', 'w') as fh:
    json.dump(records, fh)


if __name__ == '__main__':
  parse_pdf()
