import os
import argparse
import time
import hashlib
import json
import re
import sys
from io import BytesIO

import requests
from ediblepickle import checkpoint
from selenium import webdriver
from deepdiff import DeepDiff
from PyQt5.QtCore import QUrl  # pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QApplication  # pylint: disable=no-name-in-module
from PyQt5.QtWebEngineWidgets import QWebEngineView  # pylint: disable=no-name-in-module
from PyPDF2 import PdfFileReader
from tqdm import tqdm


def dir_path(_file_):
  return os.path.dirname(os.path.realpath(_file_))


def sha256(text):
  return hashlib.sha256(text.encode('utf8')).hexdigest()


def key_namer(args, kwargs):
  wait_free = {k: v for k, v in kwargs.items() if k != 'wait'}
  return sha256(str(args) + str(wait_free)) + '.pkl'


def selenium_key_namer(args, kwargs):
  return 'sel_' + key_namer(args, kwargs)


def webkit_key_namer(args, kwargs):
  return 'wk_' + key_namer(args, kwargs)


work_dir = os.path.join(dir_path(__file__), 'cache')
public_dir = os.path.join(dir_path(__file__), '..', 'public')


@checkpoint(key=key_namer, work_dir=work_dir)
def cache_request(url, method='GET', data=None, wait=None, is_binary=False, verify=True):  # pylint: disable=too-many-arguments
  if wait is not None:
    time.sleep(wait)
  if data:
    response = requests.request(method, url, data=data, stream=is_binary, verify=verify)
  else:
    response = requests.request(method, url, stream=is_binary, verify=verify)

  if is_binary:
    return response.content
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


class Render(QWebEngineView):  # pylint: disable=too-few-public-methods
  # https://stackoverflow.com/questions/37754138/how-to-render-html-with-pyqt5s-qwebengineview
  def __init__(self, url):
    self.html = None
    self.app = QApplication(sys.argv)
    super().__init__()
    self.loadFinished.connect(self._load_finished)
    self.load(QUrl(url))
    self.app.exec_()

  def _callable(self, data):
    self.html = data
    self.app.quit()

  def _load_finished(self, result):  # pylint: disable=unused-argument
    self.page().toHtml(self._callable)


@checkpoint(key=webkit_key_namer, work_dir=work_dir)
def cache_webkit(url, wait=None):
  if wait is not None:
    time.sleep(wait)
  html = Render(url).html
  print(html)
  return html


def to_list(item):
  if item:
    return [item]
  return []


def arg_parser():
  parser = argparse.ArgumentParser()
  parser.add_argument("--crawl", action="store_true")
  return parser.parse_args()


def decode_email(obfuscated):
  '''
  Decrypts a CloudFlare-obfuscated email address.
  https://stackoverflow.com/questions/36911296/scraping-of-protected-email
  '''
  key = int(obfuscated[:2], 16)
  return ''.join(chr(int(obfuscated[i:i + 2], 16) ^ key) for i in range(2, len(obfuscated) - 1, 2))


def diff_and_save(data, fname, verbose=True):
  fpath = os.path.join(public_dir, re.sub(r'^public/', '', fname))
  # compare with old data (if exists)
  if os.path.exists(fpath):
    with open(fpath, 'r') as cached_file:
      old_data = json.load(cached_file)
  else:
    old_data = None
  diff = DeepDiff(old_data, data)
  if verbose:
    print(f"Diff '{fname}': {diff}")

  # save new data
  with open(fpath, 'w') as cached_file:
    json.dump(data, cached_file)

  return diff


def normalize_state(data):
  ''' Return data with consistent ordering '''
  for datum in data:
    for key in datum.keys():
      if isinstance(datum[key], list):
        try:
          datum[key] = sorted(set(datum[key]))
        except TypeError:
          pass  # not hashable
  data.sort(key=lambda x: x.get('locale', ''))
  return data


def fetch_pdf_text(pdf_url):
  response = cache_request(pdf_url, is_binary=True)
  with BytesIO(response) as pdf_file:
    pdf_reader = PdfFileReader(pdf_file)
    return ''.join(page.extractText() for page in tqdm(pdf_reader.pages))
