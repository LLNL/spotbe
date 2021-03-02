
from pprint import pprint

class RunTable:
    
    def __init__(self, json_runs):
       
        self.between_table = {}
        self.encoder_index = 0
 
        for (file_name) in json_runs['Runs']:
            #pprint( file_name )
            run = json_runs['Runs'][file_name]
            run_data = run['Data']
            #pprint( run_data )

            for (time_key) in run_data:
                key_split = time_key.split('/')
                #pprint( key_split )

                for between in key_split:
                    self.between_table[ between ] = 0 
       
        self.encode_table_index()
 
        print( len(self.between_table )) 
        pprint( self.between_table )
        return None


    # between_table is the strings between the slashes
    def encode_table_index( self ):

        for between_str in self.between_table:
            self.between_table[ between_str ] = self.increment_encoder()

        return 1

    
    def increment_encoder( self ):
    
        self.encoder_index = self.encoder_index + 1 
        return "ab"
 

    def render(self):
        return "hello world"
