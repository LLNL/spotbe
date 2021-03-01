
from pprint import pprint

class RunTable:
    
    def __init__(self, json_runs):
        
        for (file_name) in json_runs['Runs']:
            pprint( file_name )
            run = json_runs['Runs'][file_name]
            run_data = run['Data']
            pprint( run_data )
         
        pprint( json_runs )
        return None
    
    def render(self):
        return "hello world"
