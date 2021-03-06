import csv
import os
import unittest
from common import dir_path, get_data_geocodes


def get_arcgis_fipscode():
  # The following file is the Michigan ARCGIS data and unlikely to change with time
  # https://gis-michigan.opendata.arcgis.com/datasets/minor-civil-divisions-cities-townships-v17a/data?geometry=-167.515%2C43.121%2C169.985%2C84.204
  with open(os.path.join(dir_path(__file__), 'data', 'Minor_Civil_Divisions.csv')) as csv_file:
    rows = list(csv.reader(csv_file))
    header = rows[0]
    rows = rows[1:]
    label_idx = header.index('FIPSCODE')
    return sorted([row[label_idx] for row in rows])


class TestMichiganFips(unittest.TestCase):
  '''
  Test that Michigan Arcgis and local county officials share fipcodes
  '''

  def test_michigan_fips(self):
    arcgis_fipscode = get_arcgis_fipscode()
    data_fipscode = get_data_geocodes('michigan.json')
    if data_fipscode:
      self.assertEqual(set(data_fipscode), set(arcgis_fipscode))


if __name__ == '__main__':
  unittest.main()
