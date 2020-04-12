from selenium import webdriver
import time
import random
import json

def goto_county(i):
  element = driver.find_element_by_xpath("//select[@name='idTown']")
  all_options = element.find_elements_by_tag_name("option")
  if i >= len(all_options):
    return False
  all_options[i].click()
  driver.find_element_by_xpath("//input[@name='SubmitCounty']").click()
  return True

def scrape_county_html():
  el = driver.find_element_by_class_name("elections")
  return el.get_attribute('outerHTML')

def go_back():
  driver.find_element_by_xpath("//input[@name='SubmitBack']").click()

def save_html(i, html):
  with open(f'results/result.{i}.html', 'w') as fh:
    fh.write(html)


if __name__ == '__main__':
  options = webdriver.ChromeOptions()
  options.add_argument('headless')
  driver = webdriver.Chrome(options=options)

  driver.get("https://elections.sos.ga.gov/Elections/countyregistrars.do")

  i = 0
  htmls = []
  while True:
    print(f"Fetching County {i}")
    success = goto_county(i)
    if not success:
      break

    wait = random.uniform(1, 3)
    time.sleep(wait)

    html = scrape_county_html()
    save_html(i, html)
    go_back()
    i += 1

  driver.close()
