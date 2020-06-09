import os

import parse_pdf
import augment
import aggregate

from common import dir_path

if __name__ == "__main__":
  records = parse_pdf.parse_pdf()
  records = augment.augment(records)
  records = aggregate.aggregate(records)
