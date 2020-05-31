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

  index = 0

  first_page_rows = []
  second_page_rows = []

  rows = first_page_rows

  for line in lines:
    # indicates next page has started
    if 'State of Oklahoma' in line:
      rows = second_page_rows

    # Edge case where one group lines does not end in empty string.
    if 'Please call CEB' in line:
      continue

    if line in sections:
      add_data = True
      index = 0
      continue
    elif line == '':
      add_data = False

    if add_data:
      if index >= len(rows):
        rows.append([line])
      else:
        rows[index].append(line)
      index += 1

  first_page_rows.extend(second_page_rows)
  return first_page_rows


def generate_county_dict_list(rows):
  counties = {}

  for row in rows:
    county = defaultdict(list)

    county_name = row[0].strip('0123456789 ')

    county['county'] = (county_name + ' County')
    county['locale'] = county['county']

    phone_number, fax_number = row[1].split(' ')

    county['phones'].append(phone_number)
    county['faxes'].append(fax_number)

    county['address'] = row[2]

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
