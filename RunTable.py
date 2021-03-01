
from pprint import pprint

class RunTable:
    
    def __init__(self, json_runs):
        
        for (file_name) in json_runs['Runs']:
            run = json_runs['Runs'][file_name]
            pprint( run )
         
        pprint( json_runs )
        return None
    
    def render(self):
        return "hello world"
