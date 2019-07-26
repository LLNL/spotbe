import argparse, json, sys, pickle, os, subprocess, getpass, urllib.parse
from functools import partial

CALIQUERY       = '/usr/gapps/spot/caliper/bin/cali-query'
CALIQUERY2      = '/usr/gapps/spot/caliper2/bin/cali-query'
TEMPLATE_NOTEBOOK = '/usr/gapps/wf/web/spot/data/JupyterNotebooks/TemplateNotebook.ipynb'
SPOT_SETTINGS_PATH = os.path.expanduser('~/.spot_settings.pk')
#INCLUS_DURATION = 'sum#time.inclusive.duration'



def _sub_call(cmd): 
    # call a subcommand in a new process and parse json results into object
    return json.loads(subprocess.check_output(cmd).decode('utf-8'))

def _cali_to_json(filepath):
    return _sub_call([CALIQUERY2 , '-q', 'format json(object)', filepath])



def _cali_func_duration(inclus_dur, filepath):
    return _sub_call([CALIQUERY , '-q', 'SELECT function,{0} WHERE function FORMAT JSON'.format(inclus_dur), str(filepath) ])


def _cali_func_topdown(filepath):
    return _sub_call([CALIQUERY ,'-q', 'SELECT * FORMAT JSON', str(filepath) ])


def _cali_list_globals(inclus_dur, filepath):
    cali_globals = _sub_call( [CALIQUERY ,'-j', '--list-globals', str(filepath) ])[0]

    # duration needs to be added to cali globals... just get from select call for now
    # just finds the highest duration in all the functions, assuming that would be the root 
    cali_globals["Inclusive Duration"] = max(item.get(inclus_dur, 0) for item in _cali_func_duration(inclus_dur, filepath))
    return cali_globals 


def hierarchical(args):
    dirpath    = args.directory
    inclus_dur = args.durationKey

    #load cache or initiate if missing
    cache = []
    filenames = args.filenames or [fname for fname in os.listdir(dirpath) if fname.endswith('.cali')]
    fpaths = [os.path.join(dirpath , fname) for fname in filenames] 

    import multiprocessing
    metaList = multiprocessing.Pool(18).map(partial(_cali_list_globals, inclus_dur), fpaths)
    dataList = multiprocessing.Pool(18).map(partial(_cali_func_duration, inclus_dur), fpaths)
    dataList = [{entry['function']: entry.get(inclus_dur, 1) for entry in item} for item in dataList]

    out = [{'meta': m, 'data': d} for (m, d) in zip(metaList, dataList)]

    # dump summary stdout
    json.dump(out, sys.stdout)

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def hierarchical2(args):
    dirpath    = args.directory

    #load cache or initiate if missing
    filenames = args.filenames or [fname for fname in os.listdir(dirpath) if fname.endswith('.cali')]
    fpaths = [os.path.join(dirpath , fname) for fname in filenames] 

    import multiprocessing

    cali_json = multiprocessing.Pool(18).map( _cali_to_json, fpaths)

    for run in cali_json:
        run['data'] = {record.pop('path', None): {key: float(val) for (key, val) in record.items() if is_number(val)} for record in run['records'] if 'path' in record }

        del run['records']

        run['meta'] = {}
        for (key, val) in run['globals'].items():
            adiakType = run['attributes'][key].get("adiak.type", None)  
            if adiakType:
                run['meta'][key] = {"value": val, "type": adiakType}
        del run['attributes']
        del run['globals']

    json.dump(cali_json, sys.stdout)




# returns a single durations hierarchy given a filepath
def durations(args):
    filepath = args.filepath
    inclus_dur = args.durationKey
    data_list = _cali_func_duration(inclus_dur, filepath)
    output = {}
    for item in data_list: 
        func_path = item["function"]
        duration = item.get(inclus_dur, 0)
        output[func_path] = max(duration, output.get(func_path, 0))
    json.dump(output, sys.stdout)   

def _getSpotSettings(dirpath):
    spot_settings = {}
    try: spot_settings = pickle.load(open(SPOT_SETTINGS_PATH, 'rb'))
    except: pass

    # get show list
    show_list = ['walltime', 'user', 'uid', 'launchdate', 'executable', 'executablepath', 'libraries', 'cmdline', 'hosthame', 'clustername', 'systime', 'cputime', 'fom' ]
    try: show_list = spot_settings[dirpath]['show']
    except: spot_settings[dirpath] = {'show': show_list}
    return spot_settings


def showChart(args):

    dirpath = args.dirpath
    chartname = args.chartname
    show = not args.hide
    
    # load spot settings from user home dir
    spot_settings = _getSpotSettings(dirpath)

    # get show list
    show_list = spot_settings[dirpath]['show']
    
    # toggle show
    if (show): 
        if chartname not in show_list:
            show_list.append(chartname)
    else: 
        try:
            show_list.remove(chartname)
        except: pass

    # save settings to user home dir
    pickle.dump(spot_settings, open(SPOT_SETTINGS_PATH, 'wb'))

def summary(args):
    dirpath    = args.filepath
    cache_path = os.path.join(dirpath , "spot_cache.pkl")

    #load cache or initiate if missing
    cache = {}
    #if os.path.exists(cache_path):
    #    try: cache = pickle.load(open(cache_path,'rb'))
    #    except:  pass
    #else:
    #    open(cache_path, 'a').close()  # touch file
    #    os.chown(cache_path, -1 , os.stat(dirpath).st_gid)
    #    os.chmod(cache_path, 0o660)


    # check for new cali files, if so add to cache and write to disk
    #cache_miss_fnames = [fname for fname in os.listdir(dirpath) if not fname in cache and fname.endswith('.cali')]
    cache_miss_fnames = [fname for fname in os.listdir(dirpath) ]
    if cache_miss_fnames:
        fpaths = [os.path.join(dirpath, fname) for fname in cache_miss_fnames if fname.endswith('.cali')]
        import multiprocessing
        cache = {**cache, **dict(zip(cache_miss_fnames, [cali_json for cali_json in multiprocessing.Pool(18).map( _cali_to_json, fpaths)]))}
        #pickle.dump(cache, open(cache_path, 'wb'))

    
    metaTypes = dict()
    for run in cache.values():
        metaTypes.update({k:v['adiak.type'] for (k,v) in run['attributes'].items() if v.get('adiak.type', None)})
    

    # layout: if filename provided then return contents,  else generate a generic one
    layout = json.load(open(args.layout)) if args.layout else _generateLayout(metaTypes)
    show_list = _getSpotSettings(dirpath)[dirpath]['show']
    for item in layout['charts']:
        item['show'] = item['dimension'] in show_list
        item['type'] = metaTypes[item['dimension']]
    for item in layout['table']:
        item['show'] = item['dimension'] in show_list
        item['type'] = metaTypes[item['dimension']]

    # data:  if file is missing data from another file then zero it out
    data = {}
    for (fname, f) in cache.items():
        globs = f['globals']
        for (metaName, metaType) in metaTypes.items():
            if not metaName in globs:
                globs[metaName] = 0 if metaType in ['int', 'double', "timeval", "date"] else ""
        data[fname] = globs 

    # dump summary stdout
    json.dump({'data': data, 'layout': layout}, sys.stdout, indent=4)

def _generateLayout(metaTypes):
    tableList = [{"dimension": name, "label": name} for (name, type_) in metaTypes.items()]
    chartList = [{"dimension": name, "title": name, "viz": _getVizType(type_)} for (name, type_) in metaTypes.items()]
    return {"charts": chartList, "table": tableList}

def _getVizType(valType):
    if valType in ['int', 'double', "timeval", "date"]:
       return "BarChart"
    else:
       return "PieChart"


def topdown(args):
    """call cali on topdown file and return a json object with function keys and objects with duration and topdown info"""
    filepath = args.filepath
    json.dump( {item["function"]:{ "duration": item["count"] 
                                 , "topdown": {k[15:]:v for (k,v) in item.items() if k.startswith("libpfm.topdown#")} 
                                 } 
                    for item in _cali_func_topdown(filepath) if "function" in item }
             , sys.stdout
             )


def mpi_trace(args):
  print(open(args.filepath).read())



def jupyter(args):

  # create notebook in ~/spot_jupyter dir

  #  - first create directory
  cali_path = args.cali_filepath
  ntbk_dir = os.path.expanduser('~/spot_jupyter')
  try:
      os.mkdir(ntbk_dir)
  except: pass

  #  - copy template (replacing CALI_FILE_NAME)
  
  ntbk_path = os.path.join(ntbk_dir, cali_path[cali_path.rfind('/')+1:cali_path.rfind(".")] + '.ipynb')
  ntbk_template_str = open(TEMPLATE_NOTEBOOK).read().replace('CALI_FILE_NAME', str(cali_path))
  open(ntbk_path, 'w').write(ntbk_template_str)

  # return Jupyterhub address
  print('https://rzlc.llnl.gov/jupyter/user/{}/notebooks/spot_jupyter/{}'.format(getpass.getuser(), urllib.parse.quote(os.path.basename(ntbk_path))))


# argparse
parser = argparse.ArgumentParser(description="sup")
subparsers = parser.add_subparsers(dest="sub_name")

summary_sub = subparsers.add_parser("summary")
summary_sub.add_argument("filepath", help="file and directory paths")
summary_sub.add_argument("--layout", help="layout json filepath")
summary_sub.set_defaults(func=summary)


showChart_sub = subparsers.add_parser("showChart")
showChart_sub.add_argument("dirpath", help="directory path of data to toggle chart")
showChart_sub.add_argument("chartname", help="chartname to toggle")
showChart_sub.add_argument("--hide", action="store_true", help="set to hide instead of show")
showChart_sub.set_defaults(func=showChart)

durations_sub = subparsers.add_parser("durations")
durations_sub.add_argument("durationKey", help="the key for the inclusive duration")
durations_sub.add_argument("filepath", help="file and directory paths")
durations_sub.set_defaults(func=durations)

hierarchical_sub = subparsers.add_parser("hierarchical")
hierarchical_sub.add_argument("directory", help="directory")
#hierarchical_sub.add_argument("durationKey", help="the key for the inclusive duration")
hierarchical_sub.add_argument("--filenames", nargs="+", help="individual filenames sep by space")
hierarchical_sub.set_defaults(func=hierarchical2)

topdown_sub = subparsers.add_parser("topdown")
topdown_sub.add_argument("filepath", help="file and directory paths")
topdown_sub.set_defaults(func=topdown)

jupyter_sub = subparsers.add_parser("jupyter")
jupyter_sub.add_argument("cali_filepath", help="create a notebook to check out a sweet cali file")
jupyter_sub.set_defaults(func=jupyter)

mpitrace = subparsers.add_parser("mpitrace")
mpitrace.add_argument("filepath", nargs="?", help="filepath to mpidata", default="/usr/gapps/wf/web/spot/data/test_mpi.json")
mpitrace.set_defaults(func=mpi_trace)




# get input names from command line args  (these are filenames and directory names)
args = parser.parse_args()
args.func(args)
