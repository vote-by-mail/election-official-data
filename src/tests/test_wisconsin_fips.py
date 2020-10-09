import csv
import os
import json
import unittest
from common import dir_path, public_dir


def get_arcgis_code():
  # The following file is the Wisconsin ARCGIS data and unlikely to change with time
  # https://data-ltsb.opendata.arcgis.com/datasets/wi-cities-towns-and-villages-july-2020
  with open(os.path.join(dir_path(__file__), 'data', 'WI_Cities_Towns_and_Villages__July_2020.csv')) as csv_file:
    rows = list(csv.reader(csv_file))
    header = rows[0]
    rows = rows[1:]
    label_idx = header.index('DOA')
    return sorted([row[label_idx] for row in rows])


def get_data_code():
  file_ = os.path.join(public_dir, 'wisconsin.json')
  if os.path.exists(file_):
    with open(file_) as json_file:
      rows = json.load(json_file)
      return sorted([row['code'] for row in rows])
  return None


class TestWisconsinCode(unittest.TestCase):
  '''
  Test that Wisconsin Arcgis and local county officials share DOA code
  '''

  def test_wisconsin_code(self):
    arcgis_code = get_arcgis_code()
    data_code = get_data_code()
    if data_code:
      self.assertEqual(set(data_code), set(arcgis_code))


if __name__ == '__main__':
  unittest.main()
