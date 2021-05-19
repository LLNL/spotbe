#! /usr/gapps/spot/venv_python/bin/python3

import sys, json, os
from pathlib import Path
from datetime import datetime

def split_spot1_file( input_dir, input_filename, output_dir_root, verbose):
    input_filename_no_ex = os.path.splitext(input_filename)[0]
    input_filename_ex = os.path.splitext(input_filename)[1]
    input_filename_fullpath = os.path.join(input_dir, input_filename)

    try:
        source_dict = {}

        with open(input_filename_fullpath, "r") as infile:
            source_dict = json.load(infile)

        if not 'XTics' in source_dict:
            if verbose > 1:
                print("Skipping non-spot1 file: {}".format(input_filename_fullpath))
            return

        idx = 0
        logged_once = False
        for date in source_dict['XTics']:
            our_date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f')
            timestamp = our_date.timestamp()

            output_dir_fullpath = os.path.join(   output_dir_root,
                                    our_date.strftime('%Y'),
                                    our_date.strftime('%m'),
                                    our_date.strftime('%d'))

            output_filename = input_filename_no_ex + "_" + str(timestamp) + input_filename_ex
            output_filename_fullpath = os.path.join(output_dir_fullpath, output_filename)

            if os.path.isfile(output_filename_fullpath):
                continue

            if verbose > 1:
                print("Processing {:50} --> {:50}".format(input_filename_fullpath, output_filename_fullpath))

            dest_dict = {}
            dest_dict["title"] = source_dict["title"]
            dest_dict["xAxis"] = source_dict["xAxis"]
            dest_dict["yAxis"] = source_dict["yAxis"]
            dest_dict["series"] = source_dict["series"]
            dest_dict["XTics"] = [date]
            dest_dict["commits"] = [ source_dict["commits"][idx] ]
            dest_dict["metadata"] = [ source_dict["metadata"][idx] ]

            for series_name in source_dict["series"]:
                try:
                    if idx < len(source_dict[series_name]):
                        dest_dict[series_name] = [ source_dict[series_name][idx] ]
                    else:
                        if not logged_once:
                            logged_once = True
                            if verbose:
                                print("Series [{:70}] Truncated after [{}] and omitted from {}".format(
                                      series_name
                                    , source_dict['XTics'][idx]
                                    , output_filename_fullpath))
                except:
                    print("Fail Series: {}[{}/{}]".format(series_name, idx, len(source_dict[series_name])))
                    return

            os.makedirs(output_dir_fullpath, exist_ok=True)
            Path(output_filename_fullpath).touch()

            with open(output_filename_fullpath, "w") as outfile:
                json.dump(dest_dict, outfile)
            idx = idx + 1

    except OSError as err:
        print("[ERROR] splitting into specified output directory {}: {}".format(input_filename_fullpath, err))
        return
    except:
        print("[ERROR] Unexpected error:", sys.exc_info()[0])
        raise

#
# Given an input directory, find all .json files and split out each test sample
# to a individual files into output_dir_root/yyyy/mm/dd/testname_timestamp.json
#
def split_spot1_files( input_dir, output_dir_root, verbose):
    json_file_paths = []

    if os.path.isdir(input_dir):
        for (dirpath, dirnames, filenames) in os.walk(input_dir):
            for fname in filenames:
                if fname.endswith('.json'):
                    split_spot1_file(dirpath, fname, output_dir_root, verbose)
    else:
        print("Input directory: {} is not a directory".format(input_dir))
        return

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Split spot1 file into discrete sample files")
    parser.add_argument("-v", "--verbose", action="count", help="Output progress")
    parser.add_argument("input_dir", help="path to spot1 files")
    parser.add_argument("output_dir_root", help="path to directory that will contain discrete spot1 files")
    args = parser.parse_args()

    verbose = 0
    if args.verbose:
        verbose = args.verbose

    split_spot1_files( args.input_dir, args.output_dir_root, verbose )
