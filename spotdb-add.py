#!/usr/bin/env python3

import json
import sys
import subprocess

from spotdb.sinadb import SpotSinaDB

def _get_json_from_cali_with_caliquery(filename):
    cmd = [ 'cali-query', '-q', 'format json(object)', filename ]
    proc = subprocess.Popen(cmd, stdout = subprocess.PIPE)
    cmdout, _ = proc.communicate()

    if (proc.returncode != 0):
        sys.exit('Command' + str(cmd) + ' exited with ' + str(proc.returncode))

    return json.loads(cmdout)


def _make_string_from_list(list_or_elem):
    if isinstance(list_or_elem, list):
        return '/'.join(list_or_elem)
    else:
        return list_or_elem


def _filter_cali_profile_record(reader, record):
    """ Filter useful data out of the profiling records
    """

    channel = record.get("spot.channel", "regionprofile")
    out = { "spot.channel" : channel }

    if channel == "regionprofile":
        out["path"] = _make_string_from_list(record.pop("path", ""))

        # only include metrics
        for k, v in record.items():
            if reader.attribute(k).is_value():
                out[k] = v
    else:
        for k, v in record.items():
            out[k] = _make_string_from_list(v)

    return out


def _get_json_from_cali(filename):
    from caliperreader import CaliperReader

    r = CaliperReader()
    r.read(filename)

    # disregard base attributes because they cause issues with a.metadata()
    keys = list(r.attributes())
    keys.remove("cali.attribute.name")
    keys.remove("cali.attribute.type")
    keys.remove("cali.attribute.prop")

    # convert caliperreader output to Spot format
    attr = { k : r.attribute(k).metadata()       for k   in keys      }
    recs = [ _filter_cali_profile_record(r, rec) for rec in r.records ]

    return { "attributes": attr, "globals": r.globals, "records": recs }


def _add(dbfile, files):
    db = SpotSinaDB(dbfile, read_only=False)

    files_to_add = db.filter_existing_entries(files)

    for califile in files_to_add:
        obj = _get_json_from_cali(califile)
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

    if (args[0] == "-h" or args[0] == "--help"):
        help()
        sys.exit()

    dbfile = args.pop()

    if not (dbfile.endswith('.sqlite') or dbfile.startswith('mysql')):
        msg = 'spotdb-add: Expected SQLite DB file (.sqlite) or SQL connection string ("mysql...") as last argument. Got ' + dbfile + '.'
        sys.exit(msg)

    _add(dbfile, args)


if __name__ == "__main__":
    main()
