#! /usr/gapps/spot/venv_python/bin/python3

import argparse, sys, json, os
from pathlib import Path
from datetime import datetime
from datetime import date

def split_spot1_file(input_dir, input_filename):
    input_filename_fullpath = os.path.join(input_dir, input_filename)

    try:
        source_dict = {}

        with open(input_filename_fullpath, "r") as infile:
            source_dict = json.load(infile)

        if not 'XTics' in source_dict:
            if args.verbose > 0:
                print("Skipping non-spot1 file: {}".format(input_filename_fullpath))
            return

        idx = 0
        logged_once = False

        output_filename = input_filename
        output_filename_fullpath = os.path.join(args.output_dir, output_filename)

        dest_dict = {}
        dest_dict["title"] = source_dict["title"]
        dest_dict["xAxis"] = source_dict["xAxis"]
        dest_dict["yAxis"] = source_dict["yAxis"]
        dest_dict["series"] = source_dict["series"]
        dest_dict["XTics"] = []
        dest_dict["commits"] = []
        dest_dict["metadata"] = []

        samples_found = False
        for d in source_dict['XTics']:
            our_date = datetime.strptime(d.split('.')[0], '%Y-%m-%d %H:%M:%S')

            if args.start and our_date < args.start:
                idx = idx + 1
                continue

            if args.end and our_date > args.end:
                break

            if args.verbose > 1:
                print("Processing {:50} --> {:50}".format(input_filename_fullpath, output_filename_fullpath))

            samples_found = True
            dest_dict["XTics"].append(d)
            dest_dict["commits"].append(source_dict["commits"][idx])
            dest_dict["metadata"].append(source_dict["metadata"][idx])

            for series_name in source_dict["series"]:
                try:
                    if idx < len(source_dict[series_name]):
                        if not series_name in dest_dict:
                            dest_dict[series_name] = []
                        dest_dict[series_name].append(source_dict[series_name][idx])
                    else:
                        if not logged_once:
                            logged_once = True
                            if args.verbose > 0:
                                print("Series [{:70}] Truncated after [{}] and omitted from {}".format(
                                      series_name
                                    , source_dict['XTics'][idx]
                                    , output_filename_fullpath))
                except OSError as err:
                    print("OS error {} - file {} series {}".format(err, output_filename_fullpath, series_name))
                    return
                except:
                    print("Unexpected error {} - file {} series {}".format(sys.exc_info()[0], output_filename_fullpath, series_name))
                    return
            idx = idx + 1

        if samples_found:
            os.makedirs(args.output_dir, exist_ok=True)
            with open(output_filename_fullpath, "w") as outfile:
                json.dump(dest_dict, outfile)

    except OSError as err:
        print("OS error {} - splitting {} --> {}".format(err, input_filename_fullpath, output_filename_fullpath))
        return
    except:
        print("Unexpected error {} - splitting {} --> {}".format(sys.exc_info()[0], input_filename_fullpath, output_filename_fullpath))
        raise

def info_spot1_file(input_dir, input_filename):
    input_filename_fullpath = os.path.join(input_dir, input_filename)

    source_dict = {}

    with open(input_filename_fullpath, "r") as infile:
            source_dict = json.load(infile)

    num_runs = 0
    start = datetime.strptime('1999-12-31', '%Y-%m-%d')
    end = start
    if not 'XTics' in source_dict:
        return (num_runs, start, end)

    logged_once = False

    num_runs = len(source_dict['XTics'])
    start = datetime.strptime(source_dict['XTics'][0].split('.')[0], '%Y-%m-%d %H:%M:%S')
    end = datetime.strptime(source_dict['XTics'][num_runs-1].split('.')[0], '%Y-%m-%d %H:%M:%S')
    return (num_runs, start, end)

def spot1_info(directory):
    tot_problems = 0
    tot_samples = 0
    first_run = datetime.strptime('2100-12-25', '%Y-%m-%d')
    last_run = datetime.strptime('1982-12-25', '%Y-%m-%d')

    for (dirpath, dirnames, filenames) in os.walk(directory):
        for fname in filenames:
            if fname.endswith('.json'):
                (samples, first, last) = info_spot1_file(dirpath, fname)
                if samples > 0:
                    tot_problems = tot_problems + 1
                    tot_samples = tot_samples + samples
                    if first < first_run:
                        first_run = first
                    if last > last_run:
                        last_run = last

    if tot_problems > 0:
        print("{} {} samples from {} problems from {} to {}".format(
              dirpath, tot_samples, tot_problems, first_run, last_run))

def split_spot1_files():
    if os.path.isdir(args.input_dir):
        for (dirpath, dirnames, filenames) in os.walk(args.input_dir):
            for fname in filenames:
                if fname.endswith('.json'):
                    split_spot1_file(dirpath, fname)

        if os.path.isdir(args.output_dir):
            spot1_info(args.output_dir)
    else:
        print("Input directory: {} is not a directory".format(args.input_dir))
        return

if __name__ == "__main__":
    global args
    parser = argparse.ArgumentParser(description="Split spot1 file into discrete sample files")
    parser.add_argument("-v", "--verbose", action="count", help="Output progress")
    parser.add_argument('--info', help="Display summary information about spot1 files in input directory")
    parser.add_argument('--start', type=lambda s: datetime.strptime(s, '%Y-%m-%d'), help="YYYY/mm/dd date of oldest test run")
    parser.add_argument('--end', type=lambda s: datetime.strptime(s, '%Y-%m-%d'), help="YYYY/mm/dd date of most recent run")
    parser.add_argument('--input_dir', help="input path to spot1 files")
    parser.add_argument('--output_dir', help="output path split spot1 files")
    args = parser.parse_args()

    if not args.verbose:
        args.verbose = 0

    if args.output_dir and args.input_dir:
        split_spot1_files()
    elif args.info:
        spot1_info(args.info)

