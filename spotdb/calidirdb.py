import os
import sys

from .spotdb_base import SpotDB
from .caliutil import read_caliper_file


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
        self.directory = dirname

        self.cache = {}

        self.global_metadata = {}
        self.metric_metadata = {}


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
        ret = []

        for (dirname, _, filenames) in os.walk(self.directory):
            for filename in filenames:
                if filename.endswith('.cali'):
                    ret.append(os.path.abspath(os.path.join(dirname, filename)))

        return ret


    def get_new_runs(self, last_read_time):
        ret = []

        for (dirname, _, filenames) in os.walk(self.directory):
            for filename in filenames:
                if not filename.endswith(".cali"):
                    continue

                filepath = os.path.abspath(os.path.join(dirname, filename))
                ctime = os.stat(filepath).st_ctime

                if ctime > last_read_time:
                    ret.append(filepath)

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
        content = read_caliper_file(filename)

        if 'spot.format.version' in content['globals']:
            channels = _get_channels(content)
            if 'timeseries' in channels:
                content["globals"]["timeseries"] = 1

            self.cache[filename] = content
            self._update_metadata(content["globals"], content["attributes"])


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
