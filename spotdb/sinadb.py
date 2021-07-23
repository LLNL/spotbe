from sina.datastore import create_datastore
from sina.utils import DataRange

def _get_run_data_from_records(records):
    """ Return run data dict from Sina DB for given records
    """

    runs = {}

    for rec in records:
        pathprofile = {}
        globals = { k: v['value'] for k, v in rec.data.items() }

        for prec in rec.user_defined['regionprofile']:
            path = prec.pop('path', None)
            if path:
                pathprofile[path] = prec

        if 'timeseries' in rec.user_defined:
            globals['timeseries'] = 1

        runs[rec.id] = { 'Data': pathprofile, 'Globals': globals }

    return runs


class SpotSinaDB:
    """ Access a Spot SQL DB through Sina
    """

    def __init__(self, filename):
        self.ds = create_datastore(filename)

    def __del__(self):
        self.ds.close()

    def get_run_data(self, last_read_time):
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


    def get_global_metadata(self):
        records = self.ds.records.find_with_type('caliper_global_attribute')
        result = { }

        for rec in records:
            if 'adiak.type' in rec.data:
                result[rec.id] = { 'type': rec.data['adiak.type']['value'] }

        return result


    def get_metric_metadata(self):
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
