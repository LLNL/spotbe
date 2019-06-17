import argparse, json, sys, pickle, os, subprocess, getpass, urllib
from pathlib import Path
from functools import partial
import math

CALIQUERY       = '/usr/gapps/spot/caliper/bin/cali-query'
TEMPLATE_NOTEBOOK = '/usr/gapps/wf/web/spot/data/JupyterNotebooks/TemplateNotebook.ipynb'
INCLUS_DURATION = 'sum#time.inclusive.duration'

def _sub_call(cmd): 
    # call a subcommand in a new process and parse json results into object
    return json.loads(subprocess.check_output(cmd).decode('utf-8'))


def _cali_func_duration(inclus_dur, filepath):
    #return _sub_call([CALIQUERY , '-q', 'SELECT function,{0} WHERE function FORMAT JSON'.format(inclus_dur), str(filepath) ])
    return  _sub_call([CALIQUERY , '-q', 'SELECT function,{0} FORMAT JSON'.format(inclus_dur), str(filepath) ])


def _cali_func_topdown(filepath):
    return _sub_call([CALIQUERY ,'-q', 'SELECT * FORMAT JSON', str(filepath) ])


def _cali_list_globals(inclus_dur, filepath):
    cali_globals = _sub_call( [CALIQUERY ,'-j', '--list-globals', str(filepath) ])[0]

    # duration needs to be added to cali globals... just get from select call for now
    # just finds the highest duration in all the functions, assuming that would be the root 
    cali_globals["Inclusive Duration"] = max( map( lambda item: item.get(inclus_dur, 0) 
                                                 , _cali_func_duration(inclus_dur, filepath)))
    return cali_globals 


def hierarchical(args):
    dirpath    = Path(args.directory)
    inclus_dur = args.durationKey

    #load cache or initiate if missing
    cache = []
    fnames = list(map(lambda fname: dirpath / fname, args.filenames) if args.filenames else [fpath for fpath in dirpath.iterdir() if fpath.name.endswith('.cali')] )

    import multiprocessing
    metaList = multiprocessing.Pool().map(partial(_cali_list_globals, inclus_dur), fnames)
    dataList = multiprocessing.Pool().map(partial(_cali_func_duration, inclus_dur), fnames)
    dataList = list(map(lambda item: {entry['function']: entry.get(inclus_dur, 0) for entry in item}, dataList))

    out =  [{'meta': m, 'data': d} for (m, d) in zip(metaList, dataList)]

    # dump summary stdout
    json.dump(out, sys.stdout)


#def hierarchical2(args):
#    dirpath    = Path(args.directory)
#    cache_path = dirpath / "spot_cache2.pkl"
#
#    #load cache or initiate if missing
#    cache = []
#    if cache_path.exists():
#        try: cache = pickle.load(cache_path.open('rb'))
#        except: pass
#    else:
#        cache_path.touch()
#        os.chown(cache_path, -1 , os.stat(dirpath).st_gid)
#        cache_path.chmod(0o660)
#
#    cached_filenames = list(map(lambda item: item['meta']['Filename'], cache))
#
#    # check for new cali files, if so add to cache and write to disk
#    cache_miss_fnames = [fpath for fpath in dirpath.iterdir() 
#                          if fpath.name.endswith('.cali') and not fpath.name in cached_filenames] 
#    if cache_miss_fnames:
#        import multiprocessing
#        metaList = multiprocessing.Pool().map(_cali_list_globals, cache_miss_fnames)
#        dataList = multiprocessing.Pool().map(_cali_func_duration, cache_miss_fnames)
#        dataList = map(lambda item: {entry['function']: entry['sum#time.inclusive.duration'] for entry in item}, dataList)
#
#        cache = [*cache, *[{'meta': m, 'data': d} for (m, d) in zip(metaList, dataList)]]
#        pickle.dump(cache, cache_path.open('wb'))
#
#    # dump summary stdout
#    json.dump(cache, sys.stdout)


# returns a single durations hierarchy given a filepath
def durations(args):
    filepath = Path(args.filepath)
    inclus_dur = args.durationKey
    data_list = _cali_func_duration(inclus_dur, filepath)
    output = {}
    for item in data_list: 
        func_path = item["function"]
        duration = item.get(inclus_dur, 0)
        output[func_path] = max(duration, output.get(func_path, 0))
    json.dump(output, sys.stdout)   


#def durations2(args):
#    import multiprocessing
#
#    filepaths = list(filter(lambda fp: fp.endswith('.cali'), args.filepaths))
#    if args.directory:
#        filepaths = list(map(lambda fp: os.path.join(args.directory, fp), filepaths))
#    file_datas = multiprocessing.Pool().map(_cali_func_duration, filepaths)
#
#    # create an dictionary of empty lists keyed by function path
#    durations = { item["function"]:[] for item in file_datas[0] }
#
#    for file_data in file_datas:
#        duration_by_func_path = {}
#        for item in file_data: 
#            func_path = item["function"]
#            duration = item[INCLUS_DURATION]
#            duration_by_func_path[func_path] = max(duration, duration_by_func_path.get(func_path, 0))
#        for (func_path, duration) in duration_by_func_path.items():
#            durations[func_path].append(duration)
#
#    json.dump({"filepaths": filepaths, "durationLists": [{"funcPath": f, "durationList": d} for (f,d) in durations.items()]}, sys.stdout)


def summary(args):
    dirpath    = Path(args.filepath)
    cache_path = dirpath / "spot_cache.pkl"

    #load cache or initiate if missing
    cache = {}
    if cache_path.exists():
        try: cache = pickle.load(cache_path.open('rb'))
        except: pass
    else:
        cache_path.touch()
        os.chown(cache_path, -1 , os.stat(dirpath).st_gid)
        cache_path.chmod(0o660)


    # check for new cali files, if so add to cache and write to disk
    cache_miss_fpaths = [fpath for fpath in dirpath.iterdir() if not fpath.name in cache and fpath.name.endswith('.cali')]
    if cache_miss_fpaths:
        import multiprocessing
        cache = {**cache, **dict(zip(cache_miss_fpaths, multiprocessing.Pool().map( _cali_list_globals, cache_miss_fpaths)))}
        pickle.dump(cache, cache_path.open('wb'))

    
    # layout: if filename provided then return contents,  else generate a generic one
    layout = ""
    if args.layout:
        layout = json.load(open(args.layout))

    else:
        def getChartItem(meta):
            name = meta[0]
            try:
                float(meta[1])
                viz = "BarChart"
            except:
                viz = "PieChart"
            return {"dimension": name, "title": name, "viz": viz}

        def getTableItem(meta):
            name = meta[0]
            return {"dimension": name, "label": name}


        #metas = list(list(cache.values())[0].items())
        metas = list(cache.values())[0].items()
        chartList = list(map(getChartItem, metas))
        tableList = list(map(getTableItem, metas))
        layout = {"charts": chartList, "table": tableList}
     
	

    # dump summary stdout
    json.dump({'data': cache, 'layout': layout}, sys.stdout)



def topdown(args):
    """call cali on topdown file and return a json object with function keys and objects with duration and topdown info"""
    filepath = Path(args.filepath)
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
  cali_path = Path(args.cali_filepath).resolve()
  ntbk_dir = Path.home() / 'spot_jupyter'
  ntbk_dir.mkdir(exist_ok=True)

  #  - copy template (replacing CALI_FILE_NAME)
  ntbk_path = ntbk_dir / (cali_path.stem + '.ipynb')
  ntbk_template_str = open(TEMPLATE_NOTEBOOK).read().replace('CALI_FILE_NAME', str(cali_path))
  open(ntbk_path, 'w').write(ntbk_template_str)

  # return Jupyterhub address
  print('https://rzlc.llnl.gov/jupyter/user/{}/notebooks/spot_jupyter/{}'.format(getpass.getuser(), urllib.parse.quote(ntbk_path.name)))


# argparse
parser = argparse.ArgumentParser(description="sup")
subparsers = parser.add_subparsers(dest="sub_name")

summary_sub = subparsers.add_parser("summary")
summary_sub.add_argument("filepath", help="file and directory paths")
summary_sub.add_argument("--layout", help="layout json filepath")
#summary_sub.add_argument("--layout", help="layout json filepath", default="/usr/gapps/wf/web/spot/data/default_layout.json")
summary_sub.set_defaults(func=summary)

durations_sub = subparsers.add_parser("durations")
durations_sub.add_argument("durationKey", help="the key for the inclusive duration")
durations_sub.add_argument("filepath", help="file and directory paths")
durations_sub.set_defaults(func=durations)

#durations2_sub = subparsers.add_parser("durations2")
#durations2_sub.add_argument("filepaths", nargs="+", help="one or more filepaths")
#durations2_sub.add_argument("--directory", help="prepend to each filepath")
#durations2_sub.set_defaults(func=durations2)

hierarchical_sub = subparsers.add_parser("hierarchical")
hierarchical_sub.add_argument("directory", help="directory")
hierarchical_sub.add_argument("durationKey", help="the key for the inclusive duration")
hierarchical_sub.add_argument("--filenames", nargs="+", help="individual filenames sep by space")
hierarchical_sub.set_defaults(func=hierarchical)

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
