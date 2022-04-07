import os
from posixpath import dirname
import sys

from .spotdb_base import SpotDB, SpotDBError
from .caliutil import read_caliper_file
from .spotv1 import read_spot_v1_contents, is_spot_v1_file, get_spot_v1_attribute_metadata


def _extract_channel_data(records, channel_name):
    ret = [ ]

    for rec in records:
        tmp = rec.copy()
        channel = tmp.pop("spot.channel", "regionprofile")

        if channel != channel_name:
            continue

        ret.append(tmp)

    return ret


def _extract_regionprofile(records):
    ret = { }

    for rec in _extract_channel_data(records, "regionprofile"):
        path = rec.pop("path", None)
        if path:
            ret[path] = rec

    return ret


def _get_channels(caliper_data):
    """ Return the set of profile data channels in the given Spot caliper data
    """

    channels = set()

    if 'spot.channels' in caliper_data["globals"]:
        cl = filter(lambda s : len(s) > 0, caliper_data["globals"]["spot.channels"])
        channels = { c for c in  cl }
    else:
        for rec in caliper_data["records"]:
            channels.add(rec.get("spot.channel", "regionprofile"))

    return channels


class SpotCaliperDirectoryDB(SpotDB):
    """ Access Spot data from a directory with Caliper files
    """

    def __init__(self, dirname):
        if not os.path.isdir(dirname):
            raise SpotDBError("{} is not a directory".format(dirname))

        self.directory = os.path.abspath(dirname)

        self.cache = {}

        self.global_metadata = {}
        self.metric_metadata = {}

        self.num_skipped_files = 0

    def __del__(self):
        if self.num_skipped_files > 0:
            print("spotdb: Skipped {} files w/o \"spot.metrics\" attribute".format(self.num_skipped_files),
                  file=sys.stderr)

    def get_global_attribute_metadata(self):
        result = {}

        for name, rec in self.global_metadata.items():
            if name.startswith('spot.') or name.startswith('cali.'):
                continue

            data = {}

            if 'adiak.type' in rec:
                data['type'] = rec['adiak.type']
            else:
                data['type'] = rec['type']

            result[name] = data

        return result


    def get_metric_attribute_metadata(self):
        result = {}

        for name, rec in self.metric_metadata.items():
            data = { 'type': rec['type'] }

            if 'attribute.alias' in rec:
                data['alias'] = rec['attribute.alias']
            if 'attribute.unit' in rec:
                data['unit'] = rec['attribute.unit']

            result[name] = data

        return result


    def get_all_run_ids(self):
        return self.get_new_runs(last_read_time=None)


    def get_new_runs(self, last_read_time):
        ret = []

        visited = set()
        for root, dirs, files in os.walk(self.directory, followlinks=True, topdown=True):
            path = os.path.realpath(root)
            if path in visited:
                continue
            visited.add(path)

            for d in dirs:
                if os.path.realpath(os.path.join(path, d)) in visited:
                    dirs.remove(d)

            for f in files:
                filepath = os.path.join(path, f)

                if f.endswith('.cali'):
                    if last_read_time is not None:
                        ctime = os.stat(filepath).st_ctime
                        add = ctime > last_read_time
                    else:
                        add = True
                
                    if add:
                        ret.append(filepath)
                elif f.endswith('.json'):
                    if is_spot_v1_file(filepath):
                        runs = self._read_spotv1(filepath)

                        if last_read_time is not None:
                            ret += [ r for r in runs if self.cache[r]["globals"]["launchdate"] > last_read_time ]
                        else:
                            ret += runs

        return ret


    def get_global_data(self, run_ids):
        ret = {}

        for run in run_ids:
            if not run in self.cache:
                self._read_califile(run)
            if run in self.cache:
                ret[run] = self.cache[run]["globals"]

        return ret


    def get_regionprofiles(self, run_ids):
        ret = {}

        for run in run_ids:
            if not run in self.cache:
                self._read_califile(run)
            if run in self.cache:
                ret[run] = _extract_regionprofile(self.cache[run]["records"])

        return ret


    def get_channel_data(self, channel_name, run_ids):
        ret = {}

        for run in run_ids:
            if not run in self.cache:
                self._read_califile(run)
            if run in self.cache:
                ret[run] = _extract_channel_data(self.cache[run]["records"], channel_name)

        return ret


    def _read_califile(self, filename):
        content = read_caliper_file(os.path.join(self.directory, filename))

        if 'spot.metrics' in content['globals']:
            channels = _get_channels(content)
            if 'timeseries' in channels:
                content["globals"]["timeseries"] = 1

            self.cache[filename] = content
            self._update_metadata(content["globals"], content["attributes"])
        else:
            self.num_skipped_files += 1
    

    def _read_spotv1(self, filename):
        content = read_spot_v1_contents(filename)

        for key, data in content.items():
            self.cache[key] = data
        
        (global_info, metric_info) = get_spot_v1_attribute_metadata()

        globals = { k: "" for k in global_info.keys() }
        globals['spot.metrics'] = ','.join(metric_info.keys())
      
        self._update_metadata(globals, { **global_info, **metric_info })

        return list(content.keys())


    def _update_metadata(self, globals, attributes):
        metrics = []

        if "spot.metrics" in globals:
            metrics.extend(filter(lambda m : len(m) > 0, globals["spot.metrics"].split(",")))
        if "spot.timeseries.metrics" in globals:
            metrics.extend(filter(lambda m : len(m) > 0, globals["spot.timeseries.metrics"].split(",")))

        for name in metrics:
            if name in attributes and name not in self.metric_metadata:
                self.metric_metadata[name] = attributes[name]

        for name in globals.keys():
            if name in attributes and name not in self.global_metadata:
                self.global_metadata[name] = attributes[name]
