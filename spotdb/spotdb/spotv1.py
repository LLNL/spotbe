from datetime import datetime
import json
import os


def get_spot_v1_attribute_metadata():
    globals = {
        'commit'     : { 'type': 'string' },
        'launchdate' : { 'type': 'date'   },
        'title'      : { 'type': 'string' },
    }

    metrics = {
        'avg#inclusive#sum#time.duration' : { 'type': 'double', 'attribute.unit': 'sec', 'attribute.alias': 'Avg time/rank' }
    }

    return (globals, metrics)

def is_spot_v1_file(filename):
    with open(filename) as f:
        try:
            obj = json.load(f)
        except:
            return False
    
    return 'XTics' in obj and 'commits' in obj


def read_spot_v1_contents(filename):
    """
    Read contents from Spot v1 json file
    """

    with open(filename) as f:
        obj = json.load(f)
    
    commits = obj.pop('commits')
    title = obj.pop('title')
    yAxis = obj.pop('yAxis')
    series = obj.pop('series')

    if 'show_exclusive' in obj:
        obj.pop('show_exclusive')

    dates = []

    for date in obj.pop('XTics'):
        split_date = date.split(".")
        split_date_pre = split_date[0]
        our_date = datetime.strptime(split_date_pre, '%Y-%m-%d %H:%M:%S').timestamp()
        int_date = int(our_date)
        str_date = str(int_date)
        dates.append( str_date )

    basename = os.path.basename(filename)
    base_key = basename[0:basename.find('.json')]

    result = {}

    for i in range(len(dates)):
        key = base_key + '-' + str(i)

        globals = {
            'launchdate' : dates[i],
            'commit'     : commits[i],
            'title'      : title,
            'json'       : '1'
        }

        records = []
        for funcpath, values in obj.items():
            # values are 2d arrays like: [ [ 0, 0.5 ], [ 0, 1.0, ], ... ]
            # We assume the outer dimension is the run, and the second element
            # in the inner dimension is the value.
            if (len(values) > i and isinstance(values[i], list) and len(values[i]) >= 2):
                records.append({ 'path': funcpath, 'avg#inclusive#sum#time.duration': values[i][1] })
        
        result[key] = { 'globals': globals, 'records': records }
    
    return result
