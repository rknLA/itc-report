from collections import OrderedDict
import csv
import gzip
import json
import logging
import os
import shutil
import sys
import zipfile


def process(input_path, cache_dir, output_path, keep_cache):
    """Process a report from input_path, and writes it to output_path"""
    logging.info('process files at {}'.format(input_path))
    file_paths = unzip_top_level_report(input_path, cache_dir)
    summary = summary_contents(file_paths)
    reports = read_region_reports(summary, file_paths)
    write_reports(reports, output_path, input_path)
    if not keep_cache:
        shutil.rmtree(cache_dir)


def unzip_top_level_report(in_zip_path, cache_dir):
    out_dir = get_zip_output_dir(in_zip_path, cache_dir)
    unzipped = unzip_file(in_zip_path, out_dir)
    logging.debug('Unzipped files: %s', unzipped)
    return unzipped


def unzip_file(in_path, out_path):
    zf = zipfile.ZipFile(in_path)
    unzipped_files = []
    for name in zf.namelist():
        dir_name, fn = os.path.split(name)
        logging.debug('unzipping %s', name)
        file_out_dir = os.path.join(out_path, dir_name)
        if not os.path.exists(file_out_dir):
            os.makedirs(file_out_dir)
        unzipped_path = zf.extract(name, file_out_dir)
        unzipped_files.append(unzipped_path)
    return unzipped_files


def read_region_reports(summary, unzipped_file_paths):
    out = [ read_region(r, unzipped_file_paths) for r in summary ]
    return out


def read_region(region_summary, unzipped_file_paths):
    name = region_summary['Region']
    file_name = region_summary['iTunes Store Report']

    out = OrderedDict([
        ('region', name),
        ('file_name', file_name),
    ])

    file_path = resolve_unzipped_file_path(file_name, unzipped_file_paths)
    if not file_path:
        logging.warn("Couldn't find file for region: %s", name)
        return out
    out['source_path'] = file_path

    file_contents = read_gzip(file_path)
    report = parse_region_report(file_contents)
    out['report'] = report
    return out


def resolve_unzipped_file_path(name, unzipped_paths):
    if name == 'not found':
        # this happens occassionally for INR (for example)
        return None
    for path in unzipped_paths:
        if name in path:
            return path
    raise ValueError(
            "Unzipped file name {} not found in unzipped paths! {}".format(
                name, unzipped_paths))


def read_gzip(file_path):
    with gzip.open(file_path, 'rb') as f:
        contents = f.read()
    return contents


def parse_region_report(content):
    """Region reports are tab-delimited csv-style files"""
    lines = content.splitlines()
    header_line = lines[0]
    header = header_line.split('\t')

    out = {
        'rows': [],
        'totals': {},
    }

    row_content = lines[1:-3]
    for row in row_content:
        vals = row.split('\t')
        row_data = zip(header, vals)
        row_dict = OrderedDict(row_data)
        out['rows'].append(row_dict)

    totals_lines = lines[-3:]
    for t in totals_lines:
        k, v = t.split('\t')
        out['totals'][k] = v

    return out


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
        rows = [ sanitize_row(r) for r in summary_reader ]
    return rows


def sanitize_row(row_dict):
    """Apple's wonderful CSV files are comma-AND-tab delimited"""
    out = { k.strip(): v.strip() for k, v in row_dict.iteritems() }
    return out


def find_summary(unzipped_files):
    for path in unzipped_files:
        if 'Summary.csv' in path:
            return path
    raise ValueError(
            "Summary not found in unzipped files: {}".format(unzipped_files))


def write_reports(reports, output_dest, input_path):
    """Write reports to output_dest.

    If output_dest is a dir, the filename is inferred from `input_path`
    """
    if output_dest is None:
        logging.info("no output dest, writing to stdout")
        out_file = sys.stdout
    else:
        logging.info("Writing reports to %s", output_dest)
        output_path = resolve_output_file(output_dest, input_path)
        out_file = open(output_path, 'w')
    try:
        json.dump(reports, out_file, indent=2, sort_keys=False,
                  ensure_ascii=False)
    finally:
        if output_dest is not None:
            out_file.close()


def resolve_output_file(output_dest, input_path):
    if os.path.isdir(output_dest) or os.path.basename(output_dest) == '':
        input_basename = os.path.basename(input_path)
        input_fn, ext = os.path.splitext(input_basename)
        filename = '{}-report.json'.format(input_fn)
        output_dest = os.path.join(output_dest, filename)
    output_dir = os.path.dirname(output_dest)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dest
