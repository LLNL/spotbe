import json
import sys

def _read_cali_with_caliquery(filename):
    import subprocess

    cmd = [ 'cali-query', '-q', 'format json(object)', filename ]
    proc = subprocess.Popen(cmd, stdout = subprocess.PIPE)
    cmdout, _ = proc.communicate()

    if (proc.returncode != 0):
        sys.exit('Command' + str(cmd) + ' exited with ' + str(proc.returncode))

    return json.loads(cmdout)

def _make_value(attribute, val):
    type = attribute.attribute_type()
    if type == 'int' or type == 'uint':
        return int(val)
    elif type == 'double':
        return float(val)
    else:
        return val

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
    out["path"] = _make_string_from_list(record.pop("path", ""))

    if channel == "regionprofile":
        # only include metrics
        for k, v in record.items():
            attr = reader.attribute(k)
            if attr.is_value():
                out[k] = _make_value(attr, v)
    else:
        for k, v in record.items():
            attr = reader.attribute(k)
            if attr.is_value():
                out[k] = _make_value(attr, v)
            else:
                out[k] = _make_string_from_list(v)

    return out


def read_caliper_file(filename):
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
