import csv
import logging
import os
import zipfile


def process(input_path, cache_dir, output_path, wipe_cache):
    """Process a report from input_path, and writes it to output_path"""
    logging.info('process files at {}'.format(input_path))
    file_paths = unzip_report(input_path, cache_dir)
    logging.info('Unzipped files: %s', file_paths)
    summary = summary_contents(file_paths)
    import pdb; pdb.set_trace()
    logging.debug("summary: %s", summary)


def unzip_report(in_zip_path, cache_dir):
    out_dir = get_zip_output_dir(in_zip_path, cache_dir)
    zf = zipfile.ZipFile(in_zip_path)
    unzipped_files = []
    for name in zf.namelist():
        dir_name, fn = os.path.split(name)
        logging.debug('unzipping %s', name)
        file_out_dir = os.path.join(out_dir, dir_name)
        if not os.path.exists(file_out_dir):
            os.makedirs(file_out_dir)
        unzipped_path = zf.extract(name, file_out_dir)
        unzipped_files.append(unzipped_path)
    return unzipped_files


def get_zip_output_dir(in_path, cache_path):
    basename = os.path.basename(in_path)
    in_file_name, ext = os.path.splitext(basename)
    out_path = os.path.join(cache_path, in_file_name)
    if not os.path.exists(out_path):
        os.makedirs(out_path)
    return out_path


def summary_contents(unzipped_files):
    summary_path = find_summary(unzipped_files)
    with open(summary_path, 'rb') as f:
        summary_reader = csv.DictReader(f)
        rows = list(summary_reader)
    return rows


def find_summary(unzipped_files):
    for path in unzipped_files:
        if 'Summary.csv' in path:
            return path
    raise ValueError(
            "Summary not found in unzipped files: {}".format(unzipped_files))
