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

def makes_lines(text):
  lines = []
  line = ''
  for character in text:
    if character == '\n':
      lines.append(line)
      line = ''
      continue
    line += character

  # remove header
  return lines[5:]


def group_rows(lines):
  add_data = False
  # There is no email address, and fax and phone share a line.
  sections = ['COUNTY', 'PHONE', 'MAILING ADDRESS']

  # index dictates which row this line should correspond to.  reset_index is how much we should 
  # subtract from the index to 'reset' (40 on the first page, 37 on the second page)
  reset_index = 40
  index = 40
  rows = []

  for line in lines:
    if 'State of Oklahoma' in line:
      index = 77
      reset_index = 37

    if 'Please call CEB' in line:
      continue

    if line in sections:
      add_data = True
      index -= reset_index
      continue
    elif line == '':
      add_data = False

    if add_data:
      if index >= len(rows):
        rows.append([line])
      else:
        rows[index].append(line)
      index += 1

  return rows

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
  lines = makes_lines(text)
  rows = group_rows(lines)
  counties = generate_county_dict_list(rows)

  return counties


if __name__ == '__main__':
  main()
