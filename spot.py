#! /usr/gapps/spot/venv_python/bin/python3

import argparse, json, sys, os, platform, subprocess, getpass, urllib.parse, socket, time
import cProfile

from datetime import datetime

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
architecture = platform.uname().machine
cali_query_path = dd + 'caliper/' + architecture + '/bin'
cali_query_replace = dd + 'caliper/\\" + machine + \\"/bin'

CONFIG = { 'caliquery': cali_query_path + '/cali-query'
         , 'template_notebook': dd + 'templates/TemplateNotebook_hatchet-singlecali.ipynb'
         , 'multi_template_notebook': dd + 'templates/TemplateNotebook_hatchet-manycali.ipynb'
         , 'jupyter_port': 0
         , 'jupyter_host': ''
         , 'jupyter_use_token': True
         , 'jupyter_token': ''
         }


def _sub_call(cmd):
    # call a subcommand in a new process and parse json results into object
    return json.loads(subprocess.check_output(cmd).decode('utf-8'))

def _cali_to_json(filepath):

    cali_json = _sub_call([CONFIG['caliquery'] , '-q', 'format json(object)', filepath])
    return cali_json

def _cali_timeseries_to_json(filepath):
    
    query = 'format json(object) where spot.channel=timeseries'
    cali_json = _sub_call([CONFIG['caliquery'] , '-q', query, filepath])
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

    jdict = {}
    if (use_token and not token) or (port == 0):
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
    if port == 0:
        resultdict["port"] = jdict["port"]
    else:
        resultdict["port"] = port
    if host:
        resultdict["server"] = host
    return resultdict

def multi_jupyter(args):

    # create notebook in ~/spot_jupyter dir

    #  - first create directory
    cali_path = args.cali_filepath
    cali_keys = json.loads(args.cali_keys)
    isContainer = args.container

    if isContainer:
        multi_cali_files = [{ 'cali_file'  : os.path.join(cali_path, cali_key)
                            , 'metric_name': defaultKey(os.path.join(cali_path, cali_key))
                            } 
                              for cali_key in cali_keys
                           ]

        ntbk_template_str = (open(CONFIG['multi_template_notebook']).read()
                                .replace('MUTLI_CALI_FILES', '"CALI_FILES = {}\\n"'.format(json.dumps(multi_cali_files, indent=2).replace('"', '\\"').replace('\n','\\n')))
                                .replace('CALI_METRIC_NAME', multi_cali_files[0]['metric_name'])
                                .replace('CALI_QUERY_PATH', '/usr/gapps/spot/caliper-install/bin')
                                .replace('DEPLOY_DIR', '/usr/gapps/spot/')
                            )

        os.makedirs('/notebooks',exist_ok=True)

        fullpath = '/notebooks/combo.ipynb'
        open(fullpath, 'w').write(ntbk_template_str)

        jsonret = get_jupyter_info()
        jsonret["path"] = fullpath
        print(json.dumps(jsonret))

    else:
        ntbk_dir = os.path.expanduser('~/spot_jupyter')
        try:
            os.mkdir(ntbk_dir)
        except: pass

        #  - copy template (replacing CALI_FILE_NAME)
        #metric_name = defaultKey(str(cali_path))
        path = cali_path[ cali_path.rfind('/')+1:cali_path.rfind(".") ]
        path = "combo"

        line_strs = '"CALI_FILES = [ '
        loop0 = 0
        first_metric_name = ""

        for i in sorted(cali_keys):
            full_c_path = cali_path + '/' + i
            metric_name = defaultKey(str(full_c_path))

            if loop0 == 0:
                first_metric_name = metric_name

            dira = cali_path + '/' + i
            line_strs = line_strs + '\\n { \\"cali_file\\": \\"' + dira + '\\", \\"metric_name\\": \\"' + metric_name + '\\"}, '
            loop0 = loop0 + 1


        line_strs = line_strs + '\\n]\\n"'

        ntbk_path = os.path.join(ntbk_dir, path + '.ipynb')
        ntbk_template_str = open(CONFIG['multi_template_notebook']).read()
        ntbk_template_str = ntbk_template_str.replace('MUTLI_CALI_FILES', line_strs )
        ntbk_template_str = ntbk_template_str.replace('CALI_METRIC_NAME', str(first_metric_name))
        ntbk_template_str = ntbk_template_str.replace('CALI_QUERY_PATH', cali_query_replace)

        dd = get_deploy_dir()
        ntbk_template_str = ntbk_template_str.replace('DEPLOY_DIR', dd)

        open(ntbk_path, 'w').write(ntbk_template_str)

        # return Jupyterhub address
        rz_or = "rz" if socket.gethostname().startswith('rz') else ""
        end_path = urllib.parse.quote(os.path.basename(ntbk_path))

        if args.ci_testing:
            print(ntbk_path)
        else:
            print('https://{}lc.llnl.gov/jupyter/user/{}/notebooks/spot_jupyter/{}'.format( rz_or, getpass.getuser(), end_path ))

def jupyter(args):

    # create notebook in ~/spot_jupyter dir

    #  - first create directory
    cali_path = args.cali_filepath
    isContainer = args.container

    if isContainer:
        metric_name = defaultKey(str(cali_path))
        subextension = cali_path[:cali_path.rfind(".")] + '.ipynb'
        ntbk_fullpath = os.path.normpath(os.path.join('/notebooks', *subextension.split(os.sep)))
        (ntbk_path, ntbk_name) = os.path.split(ntbk_fullpath)

        ntbk_template_str = open(CONFIG['template_notebook']).read().replace('CALI_FILE_NAME', str(cali_path)).replace('CALI_METRIC_NAME', str(metric_name))
        ntbk_template_str = ntbk_template_str.replace('CALI_QUERY_PATH', '/usr/gapps/spot/caliper-install/bin')
        ntbk_template_str = ntbk_template_str.replace('DEPLOY_DIR', '/usr/gapps/spot/')

        os.makedirs(ntbk_path,exist_ok=True)
        open(ntbk_fullpath, 'w').write(ntbk_template_str)

        jsonret = get_jupyter_info()
        jsonret["path"] = ntbk_fullpath
        print(json.dumps(jsonret))

    else:
        ntbk_dir = os.path.expanduser('~/spot_jupyter')
        try:
            os.mkdir(ntbk_dir)
        except: pass

        metric_name = defaultKey(str(cali_path))

        ntbk_name = cali_path[ cali_path.rfind('/')+1:cali_path.rfind(".") ] + '.ipynb'
        ntbk_path = os.path.join(ntbk_dir, ntbk_name)
        ntbk_template_str = open(CONFIG['template_notebook']).read().replace('CALI_FILE_NAME', str(cali_path)).replace('CALI_METRIC_NAME', str(metric_name))
        ntbk_template_str = ntbk_template_str.replace('CALI_QUERY_PATH', cali_query_replace)
        
        dd = get_deploy_dir()
        ntbk_template_str = ntbk_template_str.replace('DEPLOY_DIR', dd)

        open(ntbk_path, 'w').write(ntbk_template_str)

        # return Jupyterhub address
        rz_or = "rz" if socket.gethostname().startswith('rz') else ""
        end_path = urllib.parse.quote(os.path.basename(ntbk_path))

        if args.ci_testing:
            print(ntbk_path)
        else:
            print('https://{}lc.llnl.gov/jupyter/user/{}/notebooks/spot_jupyter/{}'.format( rz_or, getpass.getuser(), end_path ))


def _prependDir(dirpath, fnames):
    return [os.path.join(dirpath, fname) for fname in fnames]


def _getAdiakType(run, global_):
    try: return run['attributes'][global_]["adiak.type"]
    except: return None

def _getAllDatabaseRuns(dbFilepath: str, lastRead: int):
    if dbFilepath.endswith('.yaml'):
        import yaml
        import mysql.connector
        dbConfig = yaml.load(open(dbFilepath), Loader=yaml.FullLoader)
        mydb = mysql.connector.connect(**dbConfig)
        db_placeholder = "%s"
    else:
        import sqlite3
        mydb = sqlite3.connect(dbFilepath)
        db_placeholder = "?"

    cursor = mydb.cursor()

    # get runs
    runs = {}
    runNum = int(lastRead)
    cursor.execute('SELECT run, globals, records FROM Runs Where run > ' + db_placeholder, (runNum,))
    for (runNum, _globals, record) in cursor:
        runData = {}
        for rec in json.loads(record):
            funcpath = rec.pop('path', None)
            if funcpath:
                runData[funcpath] = rec

        runGlobals = json.loads(_globals)
        runs[runNum] = {'Globals': runGlobals, 'Data': runData}

    # get global meta
    cursor.execute('SELECT name, datatype FROM Metadata')
    runGlobalMeta = {name: {'type': datatype} for (name, datatype) in cursor if datatype is not None}

    return { 'Runs': runs
           # 'RunDataMeta': runNum
           , 'RunGlobalMeta': runGlobalMeta
           , 'RunSetMeta': {'LastReadPosix': runNum}
           }

def _getAllCaliRuns(filepath, subpaths):
    import multiprocessing

    cali_json = []
    try:
        cali_json = multiprocessing.Pool(18).map( _cali_to_json, _prependDir(filepath, subpaths))
    except:
        for fp in _prependDir(filepath, subpaths):
            cali_json.append(_cali_to_json(fp))

    # process all new files to transfer to front-end
    runs = {}
    runDataMeta = {}
    runGlobalMeta = {}

    for (subpath, run) in zip(subpaths, cali_json):

        runData = {}
        runGlobals = {}

        # get runData and runDataMeta
        for record in run['records']:
            funcpath = record.pop('path', None)
            if funcpath:
                runData[funcpath] = record
        for metricName in list(runData.items())[0][1]:
            runDataMeta[metricName] = {'type': run['attributes'][metricName]["cali.attribute.type"]}

        # get runGlobals and runGlobalMeta
        for (global_, val) in run['globals'].items():
            adiakType = _getAdiakType(run, global_)
            
            if global_ == "spot.options":
                if val == "timeseries":
                    runGlobals['timeseries'] = 1

            if adiakType:
                runGlobals[global_] = val
          
                runGlobalMeta[global_] = {'type': adiakType}

        # collect run
        runs[subpath] = { 'Data': runData
                      , 'Globals': runGlobals
                      }

    # output new data
    return { 'Runs': runs
           , 'RunDataMeta': runDataMeta
           , 'RunGlobalMeta': runGlobalMeta
           }

def _getAllJsonRuns(filepath, subpaths):
    output = {}
    runs = {}

    idx = -1  
    for subpath in subpaths:
        from pprint import pprint

        try:
            data = json.load(open(os.path.join(filepath, subpath)))
            commits = data.pop('commits')
            title = data.pop('title')
            yAxis = data.pop('yAxis')

            show_is_exclusive = data.get('show_exclusive', 'Default')
 
            if show_is_exclusive != 'Default': 
                 show_exclusive = data.pop('show_exclusive')

            series = data.pop('series')

            #pprint( subpath )
            #pprint( title )

            dates = []
            the_key = subpath

            for date in data.pop('XTics'):
 
                 #pprint(date)
                 split_date = date.split(".")
                 split_date_pre = split_date[0]
                 our_date = datetime.strptime(split_date_pre, '%Y-%m-%d %H:%M:%S').timestamp()
                 int_date = int(our_date)
                 str_date = str(int_date)
                 dates.append( str_date )




            idx = idx + 1
            com = commits[ idx ]
            launchdate = dates[ idx ] 

            runs[the_key] = { 'Globals': { 'launchdate': launchdate
                                                            , 'commit':  com
                                                            , 'title': title
                                                            }
                                                , 'Data': {}
                                                }
            #pprint( dates ) 
            #dates = [str(int(datetime.strptime(date, '%a %b %d %H:%M:%S %Y\n').timestamp())) for date in data.pop('XTics')]
 
            runSetName = subpath[0:subpath.find('.json')]

            for i in range(len(dates)):
                runs[runSetName + '-' + str(i)] = { 'Globals': { 'launchdate': dates[i]
                                                            , 'commit': commits[i]
                                                            , 'title': title
                                                            }
                                                , 'Data': {}
                                                }

            #pprint(runs)

            for funcpath, values in data.items():


                #print( 'for funcpath(' + funcpath + ') values in data.items()' )
                for value in values:

                    #launchdate = dates[ idx2 ]
                    #idx2=idx2 + 1
                    #suffix = value[0] if value[0] else i
                    #loopKey = runSetName + '-' + str(suffix)

                    val0 = 0
                    if type(value) is list:
                         val0 = value[0]
                
                    val1 = 0 
                    if type(value) is list:
                         val1 = value[1]
          
                    #val0 = value[0]
                    #val1 = value[1]

                    rkey = runSetName + '-' + str(val0)

                    if rkey in runs: 
                        #runs[rkey]['Data']['main'] = {'yAxis': 0}
                        #if val1 > 0.5:
                        runs[rkey]['Data'][funcpath] = {'yAxis': val1}
         
                    #runs[rkey]['Data']['main'] = {yAxis: 0}
                    #runs[rkey]['Data'][funcpath] = {'yAxis': val1}

        except:
            debugi = 1 
            if debugi == 1:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print('While processing subpath: ' + subpath)
                print('the_key=' + str(the_key))
                print('title=' + title)
                print('line_no=' + str(exc_tb.tb_lineno) )
                print('Exception occurred:')
                print('funcpath=' + funcpath)
                pprint(exc_obj)
                pprint(value)
                pprint( type(value))
                pprint(values)
                print()



    #pprint(runs)
    return { 'Runs': runs
           , 'RunDataMeta': {'yAxis': {'type': 'double'}}
           , 'RunGlobalMeta': { 'launchdate': {'type': 'date'}
                              , 'commit': {'type': 'string'}
                              }
           }


def memoryGraph(args):

    cali_path = args.cali_filepath

    #dd = get_deploy_dir()
    #opdat = open( dd + '/templates/lo.json').read()

    #filepath = "/usr/gapps/spot/datasets/lulesh_gen/100/33.cali"
    filepath = "/g/g0/pascal/spot_lulesh_timeseries_membw_8x4b.cali"
    series = _cali_timeseries_to_json( cali_path )

    output = {}
    #output['std'] = opdat
    output['series'] = series
    output['cali_path'] = cali_path

    json.dump(output, sys.stdout, indent=4)


def update_usage_file(op):
    pself = os.path.dirname(os.path.realpath(__file__))
    usage_file_name = os.path.join(pself, 'usage.log')

    if os.path.exists(usage_file_name):
        if os.access(usage_file_name, os.W_OK):
            now = datetime.now()
            date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
            uname = getpass.getuser()
            with open(usage_file_name, "a") as myfile:
                myfile.write(date_time + ' ' + uname + ' ' + op + '\n')

def getData(args):
    update_usage_file("getData")
    dataSetKey = args.dataSetKey
    lastRead = args.lastRead or 0
    cachedRunCtimes = json.loads(args.cachedRunCtimes)
        # {subpath: cachedCtime}

    output = {}

    # sql database
    if dataSetKey.endswith(('.yaml', '.sqlite')):
        output = _getAllDatabaseRuns(dataSetKey, lastRead)

    # file directory
    else:
        lastReadTime = float(lastRead)

        # get subpaths of data files that were added since last read time
        newRuns = []
        jsonSubpaths = []
        runCtimes = {}
        for (dirpath, dirnames, filenames) in os.walk(dataSetKey):
            for fname in filenames:
                fp = os.path.join(dirpath, fname)
                newCtime = os.stat(fp).st_ctime
                dataSetKey = dataSetKey.rstrip('/')

                splitKey = dataSetKey + '/'
                runSpli = fp.split( splitKey )
                len_el = len(runSpli)

                #print("len = " + str(len_el))

                if 1 < len_el:
                	runKey = runSpli[1]
                else:
                        print( "I cannot split this filename: " + fp + " with splitKey = " + splitKey )
                        exit()

                if fname.endswith('.cali'):
                    runCtimes[runKey] = newCtime
                    if newCtime > cachedRunCtimes.get(runKey, 0):
                        newRuns.append(runKey)

                if fname.endswith('.json'):
                    jsonSubpaths.append(runKey)

        deletedRuns = set(cachedRunCtimes.keys()).difference(set(runCtimes.keys()))

        if jsonSubpaths:
            output = _getAllJsonRuns(dataSetKey, jsonSubpaths)
        if newRuns:
            output = _getAllCaliRuns(dataSetKey, newRuns)

        output['deletedRuns'] = list(deletedRuns)
        output['runCtimes'] = runCtimes
        output['testingX'] = "2"

    json.dump(output, sys.stdout, indent=4)
    #json.dumps(output)


def getRun(runId, db=None):
    # sql database
    if db:
        if db.endswith('.yaml'):
            import yaml
            import mysql.connector
            dbConfig = yaml.load(open(db), Loader=yaml.FullLoader)
            mydb = mysql.connector.connect(**dbConfig)
            db_placeholder = "%s"
        else:
            import sqlite3
            mydb = sqlite3.connect(db)
            db_placeholder = "?"

        cursor = mydb.cursor()

        # get run
        cursor.execute('SELECT globals, records FROM Runs Where run = ' + db_placeholder, (runId,))
        rec = next(cursor)
        runGlobals = json.loads(rec[0])
        runData = json.loads(rec[1])
        output = {'records': runData, 'globals': runGlobals}

    # .cali file directory
    else:
        output = _cali_to_json(runId)
        del output['attributes']
    return output


def getHatchetLiteral(runId, db=None):
    funcPathDict = {line.pop('path'): line for line in getRun(runId, db)['records'] if line.get('path', None)}

    def buildTree(nodeName):
        node = {}
        node['name'] = nodeName.split('/')[-1]
        node['metrics'] = funcPathDict[nodeName]
        childrenPaths = [childPath for childPath in funcPathDict.keys()
                         if len(childPath.split('/')) == len(nodeName.split('/')) + 1 and childPath.startswith(nodeName)]
        if childrenPaths:
            node['children'] = [buildTree(childPath) for childPath in childrenPaths]
        return node

    return [buildTree(min(funcPathDict.keys()))]


if __name__ == "__main__":

    # argparse
    parser = argparse.ArgumentParser(description="utility to access data from .cali files/directory or database")
    parser.add_argument("--config", help="filepath to yaml config file")
    parser.add_argument("--container", action="store_true", help="use if running container version of spot")
    parser.add_argument("--ci_testing", help="get notebook path for CI tests", action="store_true")
    subparsers = parser.add_subparsers(dest="sub_name")

    memory_sub = subparsers.add_parser("memory")
    memory_sub.add_argument("cali_filepath", help="create a notebook to check out a sweet cali file")
    #memory_sub.add_argument("count", help="enter memory count")
    memory_sub.set_defaults(func=memoryGraph)

    jupyter_sub = subparsers.add_parser("jupyter")
    jupyter_sub.add_argument("cali_filepath", help="create a notebook to check out a sweet cali file")
    jupyter_sub.set_defaults(func=jupyter)

    multi_jupyter_sub = subparsers.add_parser("multi_jupyter")
    multi_jupyter_sub.add_argument("cali_filepath", help="create a notebook to check out a sweet cali file")
    multi_jupyter_sub.add_argument("cali_keys", help="cali filenames used to construct the multi jupyter")
    multi_jupyter_sub.set_defaults(func=multi_jupyter)

    getData_sub = subparsers.add_parser("getData")
    getData_sub.add_argument("dataSetKey",  help="directory path of files, or yaml config file")
    getData_sub.add_argument("cachedRunCtimes",  help="list of subpaths with timestamps")
    getData_sub.add_argument("--lastRead",  help="posix time with decimal for directories, run number for database")
    getData_sub.set_defaults(func=getData)

    getRun_sub = subparsers.add_parser("getRun")
    getRun_sub.add_argument("runId",  help="filepath or db run number")
    getRun_sub.add_argument("--db",  help="yaml config file, or sqlite DB")
    getRun_sub.set_defaults(func=lambda args: json.dump(getRun(args.runId, args.db), sys.stdout, indent=4))

    args = parser.parse_args()
    if args.config:
        import yaml
        CONFIG.update(yaml.load(open(args.config), Loader=yaml.FullLoader))
    args.func(args)
