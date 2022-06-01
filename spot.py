#!/usr/gapps/spot/venv_python/bin/python3
import argparse, json, sys, os, platform, subprocess, getpass, urllib.parse, socket, time
import cProfile
import hashlib
import base64

from pprint import pprint

from datetime import datetime
import sys



def get_deploy_dir():
    is_live = 1
    pre_dir = '/usr/gapps/spot/'

    if '/sand/' in __file__:
        return pre_dir + 'sand/'

    if '/dev/' in __file__:
        is_live = 0

    deploy_dir = 'live/' if is_live == 1 else 'dev/'
    return pre_dir + deploy_dir



# print( get_deploy_dir() )

dd = get_deploy_dir()

sys.path.append(dd)
sys.path.append(dd + '/spotdb')
sys.path.append('/usr/gapps/spot/venv_python/lib/python3.7/site-packages')

#  this will handle the case where: No module found named "spotdb", "caliperreader"
#  for container
sys.path.append('/usr/gapps/spot/spotdb')
#sys.path.append('/usr/gapps/spot/Caliper/python/caliper-reader')

#  this is where the new caliper-reader is located.
sys.path.append('/usr/local/lib/python3.8/dist-packages')


architecture = platform.uname().machine
cali_query_path = dd + 'caliper/' + architecture + '/bin'
cali_query_replace = dd + 'caliper/\\" + machine + \\"/bin'

CONFIG = { 'caliquery': cali_query_path + '/cali-query'
         , 'template_notebook': dd + 'templates/TemplateNotebook_HatchetSpotDBSingle.ipynb'
         , 'multi_template_notebook': dd + 'templates/TemplateNotebook_HatchetSpotDB.ipynb'
         , 'jupyter_port': 0
         , 'jupyter_host': ''
         , 'jupyter_lookup_host': False
         , 'jupyter_base_url': ''
         , 'jupyter_use_token': True
         , 'jupyter_token': ''
         , 'use_jupyterhub': True
         , 'usage_logging_dir': '/usr/gapps/spot/logs'
         }


def _sub_call(cmd):
    # call a subcommand in a new process and parse json results into object
    return json.loads(subprocess.check_output(cmd).decode('utf-8'))

def _cali_to_json(filepath):
    cali_json = _sub_call([CONFIG['caliquery'] , '-q', 'format json(object)', filepath])
    return cali_json


def defaultKey(filepath):

    records = _cali_to_json(filepath)['records']
    if len(records) == 0:
        return ""

    #c_obj = _cali_to_json(filepath)
    #metrics = c_obj['globals']['spot.metrics']
    #key = metrics.split(',')[0]
    #return key

    key_list = list(records[0].keys())
    key = (key_list[0])

    if key_list[0] == "spot.channel" and len(key_list) > 1:
        return key_list[1]

    return key


def get_jupyter_info():
    jsonstr = ""
    port = CONFIG['jupyter_port']
    host = CONFIG['jupyter_host']
    use_token = CONFIG['jupyter_use_token']
    token = CONFIG['jupyter_token']
    lookup_jupyter = CONFIG['jupyter_lookup_host']
    jupyter_base = CONFIG['jupyter_base_url']
    use_jupyterhub = CONFIG['use_jupyterhub']

    jdict = {}
    if (use_token and not token) or (port == 0 and not lookup_jupyter):
        path = os.getenv("JUPYTERSERVER")
        if not path or not os.access(path, os.R_OK):
            dir = subprocess.check_output(["/opt/conda/bin/jupyter", "--runtime-dir"]).decode("utf8").rstrip()
            candidates = [f for f in os.listdir(dir) if "nbserver" in f and ".json" in f]
            if not candidates or len(candidates) > 1:
                return {}
            path = os.path.join(dir, candidates[0])

        try:
            jsonstr = open(path, 'r').read()
            jdict = json.loads(jsonstr)
        except:
            pass

    resultdict = {}
    if use_token:
        if not token:
            resultdict["token"] = jdict["token"]
        else:
            resultdict["token"] = token

    if not lookup_jupyter:
        if port == 0:
            resultdict["port"] = jdict["port"]
        else:
            resultdict["port"] = port
        if host:
            resultdict["server"] = host
    if jupyter_base:
        resultdict["base"] = jupyter_base
    return resultdict


def getTemplates(args):
    from CustomTemplates import CustomTemplates

    dd = get_deploy_dir()
    ct = CustomTemplates( dd )

    templates = ct.get( args.cali_filepath )
    return templates


def multi_jupyter(args):

    update_usage_file("multi_jupyter")

    #  - first create directory
    spotdb_uri = args.cali_filepath
    cali_keys = json.loads(args.cali_keys)
    spotdb_record_ids = ','.join(cali_keys)
    isContainer = args.container
    custom_template = args.custom_template

    template_to_open = ""
    #metric_name = defaultKey(str(spotdb_uri))

    if custom_template:
        template_to_open = custom_template
    elif len(cali_keys) > 1:
        template_to_open = CONFIG['multi_template_notebook']
    else:
        template_to_open = CONFIG['template_notebook']

    if isContainer:
        ntbk_template_str = (open(template_to_open).read()
                                .replace('CALI_FILE_NAME', str(spotdb_uri))
                                .replace('SPOT_SPOTDB_RECORD_IDS', spotdb_record_ids)
                                .replace('SPOT_SPOTDB_URI', spotdb_uri)
                                .replace('SPOT_DEPLOY_DIR', '/usr/gapps/spot')
                            )

        name_md5 = hashlib.md5(spotdb_record_ids.encode('utf-8')).digest()
        name = base64.urlsafe_b64encode(name_md5).decode('utf-8')
        fullpath = '/notebooks/spot/m{}.ipynb'.format(name)
        try:
            os.umask(0o133)
            open(fullpath, 'w').write(ntbk_template_str)
        except:
            pass

        jsonret = get_jupyter_info()
        jsonret["path"] = fullpath
        print(json.dumps(jsonret))

    else:
        ntbk_dir = os.path.expanduser('~/spot_jupyter')
        try:
            os.mkdir(ntbk_dir)
        except: pass

        ntbk_path = os.path.join(ntbk_dir, 'combo.ipynb')
        ntbk_template_str = open(template_to_open).read()
        ntbk_template_str = ntbk_template_str.replace('CALI_FILE_NAME', str(spotdb_uri))
        ntbk_template_str = ntbk_template_str.replace('SPOT_SPOTDB_URI', spotdb_uri )
        ntbk_template_str = ntbk_template_str.replace('SPOT_SPOTDB_RECORD_IDS', spotdb_record_ids)

        dd = get_deploy_dir()
        ntbk_template_str = ntbk_template_str.replace('SPOT_DEPLOY_DIR', dd)

        open(ntbk_path, 'w').write(ntbk_template_str)

        # return Jupyterhub address
        rz_or = "rz" if socket.gethostname().startswith('rz') else ""
        end_path = urllib.parse.quote(os.path.basename(ntbk_path))

        if args.ci_testing:
            print(ntbk_path)
        else:
            print('https://{}lc.llnl.gov/jupyter/user/{}/notebooks/spot_jupyter/{}'.format( rz_or, getpass.getuser(), end_path ))


def update_usage_file(op):
    try:
        usage_dir = CONFIG['usage_logging_dir']
        if (usage_dir != ''):
            usage_file_name = os.path.join(usage_dir, 'usage.log')

            if os.path.exists(usage_file_name):
                if os.access(usage_file_name, os.W_OK):
                    now = datetime.now()
                    date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
                    uname = getpass.getuser()
                    with open(usage_file_name, "a") as myfile:
                        myfile.write(date_time + ' ' + uname + ' ' + op + '\n')
    except:
        pass


def _prependDir(dirpath, fnames):
    return [os.path.join(dirpath, fname) for fname in fnames]


def getTimeseriesData(args):
    run_id = args.run_id

    import spotdb
    db = spotdb.connect(args.dataset)
    data = db.get_channel_data("timeseries", [ args.run_id ])
    meta = db.get_metric_attribute_metadata()

    output = {}

    if run_id in data:
        output["series"] = { "records": data[run_id], "attributes": meta }
        output["cali_path"] = run_id

    json.dump(output, sys.stdout)


def getCacheFileDate(args):

    import os

    cali_filepath = args.cali_filepath

    filename = cali_filepath + '/cacheToFE.json'
    output = {}
    mtime = 2000400500

    try:
        statbuf = os.stat( filename )
        mtime = statbuf.st_mtime
    except:

        from pprint import pprint
        exc_type, exc_obj, exc_tb = sys.exc_info()

        #print('line_no=' + str(exc_tb.tb_lineno) )
        #pprint(exc_obj)
        #print()


    output['mtime'] = mtime

    json.dump(output, sys.stdout, indent=4)


def getDictionary(args):
    dataSetKey = args.dataSetKey

    filename = dataSetKey + "/dictionary.json"

    try:
       f = open( filename )
       allJSON = f.read()
       f.close()
       print( allJSON )

    except IOError:
       print( "could not get dictionary file." )


def returnErr( is_err, err_str ):

    if is_err:
        print("ERROR: " + err_str)
        exit()


def merge(source, destination):
    """
    run me with nosetests --with-doctest file.py

    >>> a = { 'first' : { 'all_rows' : { 'pass' : 'dog', 'number' : '1' } } }
    >>> b = { 'first' : { 'all_rows' : { 'fail' : 'cat', 'number' : '5' } } }
    >>> merge(b, a) == { 'first' : { 'all_rows' : { 'pass' : 'dog', 'fail' : 'cat', 'number' : '5' } } }
    True
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            destination[key] = value

    return destination


def getData(args):
    import spotdb

    dataset_key = args.dataSetKey
    last_read = args.lastRead or 0

    from ErrorHandling import ErrorHandling

    ehandle = ErrorHandling()
    result = ehandle.check_file( dataset_key )

    if not result:
        return result

    writeToFile = args.writeToFile or 0
    cacheFilename = "cacheToFE.json"
    cachePath = dataset_key + '/' + cacheFilename

    if not writeToFile:
       try:
           f = open( cachePath )
           allJSON = f.read()
           print(allJSON)
           f.close()
           return 1

       except IOError:
           a=0  #print("File " + cachePath + " does not exists")

    db = spotdb.connect(dataset_key, read_only=True)

    runs = []

    if last_read > 0:
        runs = db.get_new_runs(last_read)
    else:
        runs = db.get_all_run_ids()

    # merge "global" and "regionprofile" records into "Runs" structure

    globals = db.get_global_data(runs)
    records = db.get_regionprofiles(runs)

    rundata = { }

    for run in runs:
        if run in globals and run in records:
            rundata[run] = { "Data": records[run], "Globals": globals[run] }

    output = {
        "Runs"          : rundata,
        "RunDataMeta"   : db.get_metric_attribute_metadata(),
        "RunGlobalMeta" : db.get_global_attribute_metadata()
    }

    #  Please do not DELETE.  this is necessary to create the cacheToFE.json
    if writeToFile == '1':

       from RunTable import RunTable

       runt = RunTable( output, 18 )
       table_text = runt.make_table_str()
       pool_text = runt.make_pool_str()

       myDictionary = json.loads( "{" + table_text + "}" )
       output['dictionary'] = myDictionary["dictionary"]

       jstr = json.dumps(output)
       pri_str = jstr

       #  Currently not using pri_str because combined directories of json and cali will result in ,,,, need to fix that before can use the optimized version:
       pri_str = '{' + table_text + ',"Runs":' + pool_text + ', "RunDataMeta":' + json.dumps(output["RunDataMeta"]) + ', "RunGlobalMeta":' + json.dumps(output["RunGlobalMeta"]) + ', "deletedRuns": [], "runCtimes":[], "foundReport":"0"}'

       #jstr = json.dumps(output)
       #pri_str = jstr
       print('wrote file to: ' + cachePath)
       f = open( cachePath, "w" )
       f.write( pri_str )
       f.close()
       return 1

    return json.dump(output, sys.stdout)


if __name__ == "__main__":

    # argparse
    parser = argparse.ArgumentParser(description="utility to access data from .cali files/directory or database")
    parser.add_argument("--config", help="filepath to yaml config file")
    parser.add_argument("--container", action="store_true", help="use if running container version of spot")
    parser.add_argument("--ci_testing", help="get notebook path for CI tests", action="store_true")
    subparsers = parser.add_subparsers(dest="sub_name")

    timeseries_sub = subparsers.add_parser("getTimeseriesData")
    timeseries_sub.add_argument("dataset", help="dataset (directory or SQL descriptor)")
    timeseries_sub.add_argument("run_id", help="run ID in the dataset")
    timeseries_sub.set_defaults(func=getTimeseriesData)

    getTemplates_sub = subparsers.add_parser("getTemplates")
    getTemplates_sub.add_argument("cali_filepath", help="create a notebook to check out a sweet cali file")
    getTemplates_sub.set_defaults(func=getTemplates)

    getCacheFileDate_sub = subparsers.add_parser("getCacheFileDate")
    getCacheFileDate_sub.set_defaults(func=getCacheFileDate)
    getCacheFileDate_sub.add_argument("cali_filepath", help="create a notebook to check out a sweet cali file")

    multi_jupyter_sub = subparsers.add_parser("multi_jupyter")
    multi_jupyter_sub.add_argument("cali_filepath", help="create a notebook to check out a sweet cali file")
    multi_jupyter_sub.add_argument("cali_keys", help="cali filenames used to construct the multi jupyter")
    multi_jupyter_sub.add_argument("--custom_template",  help="specify which template path/file to use")
    multi_jupyter_sub.set_defaults(func=multi_jupyter)

    getData_sub = subparsers.add_parser("getData")
    getData_sub.add_argument("dataSetKey",  help="directory path of files, or yaml config file")
    getData_sub.add_argument("cachedRunCtimes",  help="list of subpaths with timestamps")
    getData_sub.add_argument("--poolCount",  help="specify number of pools to use")
    getData_sub.add_argument("--writeToFile",  help="specify number of pools to use")
    getData_sub.add_argument("--maxLevels",  help="specify number of levels to show for flamecharts")
    getData_sub.add_argument("--lastRead",  help="posix time with decimal for directories, run number for database")
    getData_sub.set_defaults(func=getData)

    getDictionary_sub = subparsers.add_parser("getDictionary")
    getDictionary_sub.add_argument("dataSetKey",  help="directory path of files, or yaml config file")
    getDictionary_sub.set_defaults(func=getDictionary)

    args = parser.parse_args()
    if args.config:
        import yaml
        CONFIG.update(yaml.load(open(args.config), Loader=yaml.FullLoader))
    args.func(args)
