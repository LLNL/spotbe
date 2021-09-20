from uuid import uuid4

import sina.datastore
from sina.utils import DataRange
from sina.model import Record

from spotdb.spotdb import SpotDB

def _extract_regionprofile(regionprofile_records):
    ret = {}

    for rec in regionprofile_records:
        tmp = rec.copy()
        path = tmp.pop('path', None)
        if path:
            ret[path] = tmp

    return ret

def _get_run_data_from_records(records):
    """ Return run data dict from Sina DB for given records
    """

    runs = {}

    for rec in records:
        regionprofile = {}
        globals = { k: v['value'] for k, v in rec.data.items() }

        if 'regionprofile' in rec.user_defined:
            regionprofile = _extract_regionprofile(rec.user_defined['regionprofile'])
        if 'timeseries' in rec.user_defined:
            globals['timeseries'] = 1

        runs[rec.id] = { 'Data': regionprofile, 'Globals': globals }

    return runs


class SpotSinaDB(SpotDB):
    """ Access a Spot SQL DB through Sina
    """

    def __init__(self, filename, read_only=False):
        self.ds = sina.datastore.connect(filename, read_only=read_only)

    def __del__(self):
        self.ds.close()

    def get_all_run_data(self, last_read_time):
        """ Return a dict with region profile and global values for each
        run in the database.

        Structure:

        { 'run-id-1': {
            'Data': { 'main': { 'avg#inclusive#sum#time.duration: 42.0, ... }, ... },
            'Globals': { 'launchdate': 42424242, ... }
            },
          'run-id-2': {
              ...
            }
        }
        """

        if last_read_time is None:
            last_read_time = 0

        targets = self.ds.records.find_with_data(launchdate=DataRange(min=last_read_time))

        return _get_run_data_from_records(self.ds.records.get(targets))


    def get_global_attribute_metadata(self):
        records = self.ds.records.find_with_type('caliper_global_attribute')
        result = { }

        for rec in records:
            if 'adiak.type' in rec.data:
                result[rec.id] = { 'type': rec.data['adiak.type']['value'] }

        return result


    def get_metric_attribute_metadata(self):
        records = self.ds.records.find_with_type('caliper_metric_attribute')
        result = {}

        for rec in records:
            data = { 'type': rec.data['type']['value'] }

            if 'attribute.alias' in rec.data:
                data['alias'] = rec.data['attribute.alias']['value']
            if 'attribute.unit' in rec.data:
                data['unit'] = rec.data['attribute.unit']['value']

            result[rec.id] = data

        return result


    def get_all_run_ids(self):
        recs = self.ds.records.find_with_type("run")
        return [ r["id"] for r in recs ]


    def get_new_runs(self, last_read_time):
        recs = self.ds.records.find_with_data(launchdate=DataRange(min=last_read_time))
        return [ r["id"] for r in recs ]


    def get_global_data(self, run_ids):
        ret = {}

        for run in run_ids:
            rec = self.ds.records.get(run)
            globals = { k: v['value'] for k, v in rec.data.items() }
            ret[run] = globals

        return ret


    def get_regionprofiles(self, run_ids):
        ret = {}

        for run in run_ids:
            rec = self.ds.records.get(run)
            if 'regionprofile' in rec.user_defined:
                ret[run] = _extract_regionprofile(rec.user_defined['regionprofile'])

        return ret


    def filter_existing_entries(self, filenames):
        ret = []

        for f in filenames:
            ids = self.ds.records.find_with_file_uri(f, ids_only=True)

            _dummy = object()
            if next(ids, _dummy) == _dummy:
                ret.append(f)

        return ret


    def add(self, obj, *args, **kwargs):
        self._update_attribute_records(obj["globals"], obj["attributes"])
        rec = Record(id=str(uuid4()), type="run")

        for name, value in obj["globals"].items():
            if name.startswith("cali.") or name.startswith("spot."):
                continue

            type = obj["attributes"][name]["type"]

            if type == "int" or type == "uint":
                value = int(value)
            elif type == "double":
                value = float(value)

            rec.add_data(name, value)

        # Add profiling data

        channel_data = {}

        for entry in obj["records"]:
            channel = "regionprofile"

            if "spot.channel" in entry:
                channel = entry["spot.channel"]
                entry.pop("spot.channel")

            if not channel in channel_data:
                channel_data[channel] = []

            channel_data[channel].append(entry)

        rec.user_defined = channel_data

        filename = kwargs.get('filename', None)
        if filename is not None:
            rec.add_file(filename, tags=[ "caliper" ])

        self.ds.records.insert(rec)


    def _update_attribute_records(self, globals, attributes):
        def _update_record(name, rectype, values):
            if self.ds.records.exist(name):
                return
            rec = Record(id=name, type=rectype)
            for k,v in values.items():
                rec.add_data(k,v)
            self.ds.records.insert(rec)

        metrics = []

        if "spot.metrics" in globals:
            metrics.extend(filter(lambda m : len(m) > 0, globals["spot.metrics"].split(",")))
        if "spot.timeseries.metrics" in globals:
            metrics.extend(filter(lambda m : len(m) > 0, globals["spot.timeseries.metrics"].split(",")))

        for name in metrics:
            if name in attributes:
                _update_record(name, "caliper_metric_attribute", attributes[name])

        for name in globals.keys():
            if name in attributes:
                _update_record(name, "caliper_global_attribute", attributes[name])