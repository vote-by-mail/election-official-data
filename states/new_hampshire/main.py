import json
import scrapy
from scrapy.crawler import CrawlerProcess
import csv
import re
from io import StringIO

# We use Scrapy for New Hampshire because it has an .aspx __viewstate
# which must be generated and sent along with the request


class NewHampshireSpider(scrapy.Spider):
  name = 'New Hampshire'
  start_urls = ["https://app.sos.nh.gov/Public/Reports.aspx"]

  def parse(self, response):
    yield scrapy.FormRequest.from_response(
      response,
      formdata={
          'ctl00$MainContentPlaceHolder$PPReport': 'rdoCsv'
      },
      method="POST",
      callback=self.parse_csv
    )

  def parse_csv(self, response):
    f = StringIO(response.text)
    reader = csv.DictReader(f, delimiter=",")
    clerk_data = []

    for row in reader:
      data = self.extract_clerk_data(row)
      if data is not None:
        clerk_data.append(data)

    with open('../../public/new_hampshire.json', 'w') as f:
      json.dump(clerk_data, f)

    return clerk_data

  def extract_clerk_data(self, row):
    town_or_city = self.extract_city_without_ward(row)

    if town_or_city is None:
      return None

    email_pattern = re.compile(r"^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$")
    clerk_data_entry = {}
    clerk_data_entry["city"] = town_or_city
    clerk_data_entry["address"] = row["Address"].strip()
    clerk_data_entry["locale"] = town_or_city
    clerk_data_entry["emails"] = [row["E-Mail"]] if email_pattern.match(row["E-Mail"]) else []
    clerk_data_entry["phones"] = ["603-" + row["Phone (area code 603)"]] if row["Phone (area code 603)"] else []
    clerk_data_entry["faxes"] = ["603-" + row["Fax"]] if(row["Fax"]) else []
    clerk_data_entry["official"] = " ".join(x.capitalize() for x in row["Clerk"].split()) if row["Clerk"] else []
    return clerk_data_entry

  def extract_city_without_ward(self, row):
    capitalized_city = " ".join(x.capitalize() for x in row["Town/City"].split())

    # we only extract data from the first ward
    if " Ward 01" in capitalized_city:
      return capitalized_city.split(" Ward ")[0]
    if " Ward " in capitalized_city:
      return None

    return capitalized_city.strip()


if __name__ == "__main__":
  process = CrawlerProcess()
  process.crawl(NewHampshireSpider)
  process.start()
