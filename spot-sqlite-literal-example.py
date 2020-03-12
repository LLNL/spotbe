#!/usr/gapps/spot/venv_python/bin/python3

import hatchet as ht
import json

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

lit = getHatchetLiteral(3, "/usr/gapps/spot/datasets/lulesh_new.sqlite")
gf = ht.GraphFrame.from_literal(lit)
print(gf.dataframe)

print(list(gf.dataframe.columns))
print(gf.inc_metrics)
print(gf.exc_metrics)

# needs to pick one of the metric columns
print("metric =", gf.exc_metrics[0])
print(gf.tree(color=True, metric=gf.exc_metrics[0]))
print("")

print("metric =", gf.exc_metrics[1])
print(gf.tree(color=True, metric=gf.exc_metrics[1]))
print("")

print("metric =", gf.exc_metrics[2])
print(gf.tree(color=True, metric=gf.exc_metrics[2]))
print("")

#
