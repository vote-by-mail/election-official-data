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
    # We want to make sure the intersection is really significant (i.e.)
    # above 95%
    if data_code:
      data_code_size = len(data_code)
      arcgis_code_size = len(arcgis_code)
      intersection_size = len(list(set(arcgis_code) & set(data_code)))
      self.assertTrue(intersection_size / max(arcgis_code_size, data_code_size) > 0.95)

      # We also hardcode the divergent amount between the two, so when this
      # test fails we know something has changed in one of our sources for
      # WI
      #
      # Current values were taken at October 9 2020

      # There's 65 items on ArcGIS not present on the Election Officials Data
      self.assertTrue(len(list(set(arcgis_code) - set(data_code))) == 65)
      # There's 9 items on the Election Officials Data not present on ArcGIS
      self.assertTrue(len(list(set(data_code) - set(arcgis_code))) == 9)


if __name__ == '__main__':
  unittest.main()
