import os
import requests
import argparse
import time
import hashlib
import json

from ediblepickle import checkpoint
from selenium import webdriver
from deepdiff import DeepDiff


def dir_path(_file_):
  return os.path.dirname(os.path.realpath(_file_))

sha256 = lambda x: hashlib.sha256(x.encode('utf8')).hexdigest()

def key_namer(args, kwargs):
  wait_free = { k: v for k, v in kwargs.items() if k != 'wait' }
  return sha256(str(args) + str(wait_free)) + '.pkl'

def selenium_key_namer(args, kwargs):
  return 'sel_' + key_namer(args, kwargs)

work_dir = dir_path(__file__) + '/../../cache/'

@checkpoint(key=key_namer, work_dir=work_dir)
def cache_request(url, method='GET', data={}, wait=None, is_binary=False, verify=True):
  if wait is not None:
    time.sleep(wait)
  if data:
    response = requests.request(method, url, data=data, stream=is_binary, verify=verify)
  else:
    response = requests.request(method, url, stream=is_binary, verify=verify)

  if is_binary:
    return response.content
  else:
    return response.text
    
@checkpoint(key=selenium_key_namer, work_dir=work_dir)
def cache_selenium(url, wait=None):
  if wait is not None:
    time.sleep(wait)
  options = webdriver.ChromeOptions()
  options.add_argument('headless')
  with webdriver.Chrome(options=options) as driver:
    driver.get(url)
    return driver.page_source

def to_list(x):
  if x:
    return [x]
  else:
    return []

def arg_parser():
  parser = argparse.ArgumentParser()
  parser.add_argument("--crawl", action="store_true")
  return parser.parse_args()

def decode_email(e):
  '''
  Decrypts a CloudFlare-obfuscuated email address.
  https://stackoverflow.com/questions/36911296/scraping-of-protected-email
  '''
  de = ""
  k = int(e[:2], 16)

  for i in range(2, len(e)-1, 2):
    de += chr(int(e[i:i+2], 16)^k)

  return de

def diff_and_save(data, fname, verbose=True):
  # compare with old data (if exists)
  if os.path.exists(fname):
    with open(fname, 'r') as f:
      old_data = json.load(f)
  else:
    old_data = None
  diff = DeepDiff(old_data, data)
  if verbose:
    print(f"Diff '{fname}': {diff}")

  # save new data
  with open(fname, 'w') as f:
    json.dump(data, f)

  return diff

def normalize_state(data):
  ''' Return data with consistent ordering '''
  for datum in data:
    for key in datum.keys():
      if isinstance(datum[key], list):
        try:
          datum[key] = sorted(set(datum[key]))
        except TypeError:
          pass #not hashable
  data.sort(key=lambda x: x.get('locale',''))
  return data
