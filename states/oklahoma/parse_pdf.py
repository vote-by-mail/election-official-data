from common import cache_request
from io import BytesIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
import os
from collections import defaultdict


def get_text(url):
  req = cache_request(url, is_binary=True)
  with BytesIO(req) as fh:
    output = StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output, laparams=LAParams())
    interpreter = PDFPageInterpreter(manager, converter)

    for page in PDFPage.get_pages(fh, set()):
      interpreter.process_page(page)
    
    converter.close()
    text = output.getvalue()
    output.close()
    return text


def group_rows(lines):
  # There is no email address, and fax and phone share a line.
  sections = ['COUNTY', 'PHONE', 'MAILING ADDRESS']

  # Only add data to output if it is between one of the above sections and an empty string.
  add_data = False

  rows = {}
  rows['COUNTY'] = []
  rows['PHONE'] = []
  rows['MAILING ADDRESS'] = []

  section = ''

  for line in lines:
    # Edge case where one group lines does not end in empty string.
    if 'Please call CEB' in line:
      continue

    if line in sections:
      add_data = True
      section = line
      continue
    elif line == '':
      add_data = False

    if add_data:
      rows[section].append(line)

  assert(len(rows['COUNTY']) == len(rows['PHONE']))
  assert(len(rows['COUNTY']) == len(rows['MAILING ADDRESS']))

  return rows


def generate_county_dict_list(rows):
  counties = {}

  for i in range(0, len(rows['COUNTY'])):
    county = defaultdict(list)

    county_name = rows['COUNTY'][i].strip('0123456789 ')

    county['county'] = (county_name + ' County')
    county['locale'] = county['county']

    phone_number, fax_number = rows['PHONE'][i].split(' ')

    county['phones'].append(phone_number)
    county['faxes'].append(fax_number)

    county['address'] = rows['MAILING ADDRESS'][i]

    counties[county_name] = county

  return counties


def main():
  text = get_text('https://www.ok.gov/elections/documents/CEB_Physical%20Addresses_%283-19-2020%29.pdf')
  lines = text.split('\n')
  # remove header
  lines = lines[5:]
  rows = group_rows(lines)
  counties = generate_county_dict_list(rows)

  return counties


if __name__ == '__main__':
  main()
