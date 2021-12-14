# SpotDB: A Python module to access Spot performance data

The spotdb module accesses Spot performance data. It works with Caliper 
directories (directories with .cali files) or Spot SQL/SQLite databases.

## Creating Spot SQL database

Use `spotdb-add` to create a Spot SQL database or add Caliper .cali files to 
one:

    $ spotdb-add.py demos/test/*.cali demo.sqlite

## Reading Spot data

Use the `SpotDB` class to access Spot data:

```Python
import datetime as dt
import spotdb

db = spotdb.connect("demos.sqlite")

runs = db.get_all_run_ids()
data = db.get_regionprofiles(runs[:2])
info = db.get_global_data(runs[:2])

for run in set(data.keys()) & set(info.keys())
    launchdate = dt.datetime.fromtimestamp(info[run]["launchdate"])
    time = data.get("main", 0)
    print("Launchdate: {} Time: {}".format(launchdate, time))
```
