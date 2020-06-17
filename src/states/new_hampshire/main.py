import csv
import re
from io import StringIO
from bs4 import BeautifulSoup
from common import cache_request

BASE_URL = "https://app.sos.nh.gov/Public/Reports.aspx"

re_email = re.compile(r"^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$")


def parse_csv(text):
  csv_str = StringIO(text)
  reader = csv.DictReader(csv_str, delimiter=",")
  clerk_data = []
  for row in reader:
    data = extract_clerk_data(row)
    if data is not None:
      clerk_data.append(data)
  return clerk_data


def extract_clerk_data(row):
  town_or_city = extract_city_without_ward(row)

  if town_or_city is None:
    return None

  clerk_data_entry = {}
  clerk_data_entry["city"] = town_or_city
  clerk_data_entry["address"] = row["Address"].strip()
  clerk_data_entry["locale"] = town_or_city
  clerk_data_entry["emails"] = [row["E-Mail"]] if re_email.match(row["E-Mail"]) else []
  clerk_data_entry["phones"] = ["603-" + row["Phone (area code 603)"]] if row["Phone (area code 603)"] else []
  clerk_data_entry["faxes"] = ["603-" + row["Fax"]] if(row["Fax"]) else []
  if row["Clerk"]:
    clerk_data_entry["official"] = " ".join(x.capitalize() for x in row["Clerk"].split())
  return clerk_data_entry


def extract_city_without_ward(row):
  capitalized_city = " ".join(x.capitalize() for x in row["Town/City"].split())

  # we only extract data from the first ward
  if " Ward 01" in capitalized_city:
    return capitalized_city.split(" Ward ")[0]
  if " Ward " in capitalized_city:
    return None

  return capitalized_city.strip()


def fetch_data():
  # extract __viewstate and other form params for .aspx
  page = cache_request(BASE_URL)
  soup = BeautifulSoup(page, 'lxml')
  form = soup.find('form')
  form_data = {form_input['name']: form_input['value'] for form_input in form('input')}
  form_data['ctl00$MainContentPlaceHolder$PPReport'] = 'rdoCsv'

  csv_text = cache_request(BASE_URL, method="POST", data=form_data)
  return parse_csv(csv_text)


if __name__ == "__main__":
  print(fetch_data())
