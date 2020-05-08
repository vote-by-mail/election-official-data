import crawl
import parse

from common import arg_parser

if __name__ == '__main__':
  args = arg_parser()

  if args.crawl:
    crawl.main()
  parse.main()
