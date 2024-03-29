#!/usr/bin/env python3

import sys

from tqdm import tqdm

from spotdb.sinadb import SpotSinaDB
from spotdb.caliutil import read_caliper_file
from spotdb.sqlutil import make_sql_uri_from_cnf

def _add(dbfile, files):
    db = SpotSinaDB(dbfile, read_only=False)

    files_to_add = db.filter_existing_entries(files)

    for califile in tqdm(files_to_add,unit="files",dynamic_ncols=True):
        obj = read_caliper_file(califile)
        keys = obj.keys()

        if 'globals' not in keys or 'records' not in keys:
            sys.exit('{} is not a Spot file'.format(califile))
        if not 'spot.format.version' in obj['globals']:
            sys.exit('{} is not a Spot file: spot.format.version attribute is missing.'.format(califile))

        db.add(obj, filename=califile)

    n_added   = len(files_to_add)
    n_skipped = len(files) - n_added

    print("spotdb-add: {} record(s) added.".format(n_added))
    if n_skipped > 0:
        print("spotdb-add: {} duplicate(s) skipped.".format(n_skipped))


def help():
    print("Usage: spotdb-add.py caliper-files... sqlite3-file")


def main():
    args = sys.argv[1:]

    if (len(args) < 2):
        msg = "spotdb-add: Expected caliper-file(s) and SQL connection string arguments"
        help()
        sys.exit(msg)

    if (args[0] == "-h" or args[0] == "--help"):
        help()
        sys.exit()

    uri = args.pop()
    if uri.endswith(".cnf"):
        uri = make_sql_uri_from_cnf(uri)

    if not (uri.endswith('.sqlite') or uri.startswith('mysql')):
        msg = 'spotdb-add: Expected SQLite file (.sqlite), SQL URI ("mysql..."), or MySQL config file (.cnf) as last argument. Got ' + uri + '.'
        sys.exit(msg)

    _add(uri, args)


if __name__ == "__main__":
    main()
