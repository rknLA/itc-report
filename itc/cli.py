import argparse
import logging

from itc import report


LOG_LEVEL_MAP = {
    'critical': logging.CRITICAL,
    'error': logging.ERROR,
    'warning': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input',
            help='Which file (or directory) to process')
    parser.add_argument('-c', '--cache_dir',
            help='Where to store temporary files during processing',
            default='build/cache')
    parser.add_argument('-w', '--wipe_cache',
            help='Wipe the cache when complete?',
            type=bool,
            default=False)
    parser.add_argument('-v', '--verbosity',
            help='Logging verbosity',
            default='debug')
    parser.add_argument('-o', '--output',
            help='Where to write the output',
            default='build/')
    args = parser.parse_args()

    logging.basicConfig(level=LOG_LEVEL_MAP[args.verbosity])

    report.process(args.input,
                   args.cache_dir,
                   args.output,
                   args.wipe_cache)
