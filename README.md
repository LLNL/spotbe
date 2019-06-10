# Overview

backend is called from the frontend using lorenz endpoint:

```js
    $.ajax({
        dataType:'jsonp',
        url:     'https://rzlc.llnl.gov/lorenz/lora/lora.cgi/jsonp',
        data:   {'via'    : 'post',
                'route'  : '/command/rztopaz',
                'command': '/usr/tce/bin/python3 /usr/gapps/spot/spot.py ' + spotArgs  
                }
    }).done(function(value) { var spotReturnedValue = value.output.command_out; });
```
---

## Summary Call
>*take a directory pathname of .cali files and returns the meta data of each file*

```
usage: spot.py summary [-h] [--layout LAYOUT] filepath

positional arguments:
  filepath         file and directory paths

optional arguments:
  -h, --help       show this help message and exit
  --layout LAYOUT  layout json filepath
```

## Hierarchical Call

>*Takes a directory pathname of .cali files and returns data to the front end to display as a diveable stacked barchart and flamegraph/sankey diagram*

```
usage: spot.py hierarchical [-h] [--filenames FILENAMES [FILENAMES ...]]
                            directory durationKey

positional arguments:
  directory             directory
  durationKey           the key for the inclusive duration

optional arguments:
  -h, --help            show this help message and exit
  --filenames FILENAMES [FILENAMES ...]
                        individual filenames sep by space
```
