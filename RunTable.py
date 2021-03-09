
import math
import multiprocessing

from pprint import pprint

class RunTable:
    
    def __init__(self, json_runs):

        self.json_runs = json_runs       
        self.between_table = {}
        self.encoder_index = 0
        self.encoder_lookup = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()-=_+[]{};:,./<>?`~"
 
        for (file_name) in json_runs['Runs']:
            #pprint( file_name )
            run = json_runs['Runs'][file_name]
            run_data = run['Data']
            #pprint( run_data )
            #print( 'Data: ' + str(len( str( run['Data'] ))))
            #print( 'Globals: ' +str( len( str( run['Globals'] ))))

            for (time_key) in run_data:
		
		# typical time_key looks like:
                # "problem/cycle/all physics/advection/material model evaluate/material: al_6061/leos eos"
                key_split = time_key.split('/')
                #pprint( key_split )

                for between in key_split:

                    # typical between looks like "all physics"
                    self.between_table[ between ] = 0 
       
        self.encode_table_index()
 
        #print( len(self.between_table )) 
        #pprint( self.between_table )
        return None


    # between_table is the strings between the slashes
    def encode_table_index( self ):

        for between_str in self.between_table:
            self.between_table[ between_str ] = self.increment_encoder()

        return 1

    
    def increment_encoder( self ):
    
        self.encoder_index = self.encoder_index + 1 
        en_len = len(self.encoder_lookup)
        first = self.encoder_index / en_len
        first = math.floor( first )
        first = self.encoder_lookup[ first ]

        second = self.encoder_index % en_len
        second = self.encoder_lookup[ second ]

        return first + second



    def make_table_str(self):

        estr = ""

        for (between_str) in self.between_table:

            encoded_str = self.between_table[ between_str ]
            estr = estr + ',"' + between_str + '":"' + encoded_str + '"'

        return '"dictionary":{' + estr[1:] + '}'


    # now this takes an array of runs, each run contains a 'Data' object
    def subset_of_runs_handler(self, runs):

        compact_runs = {}

        for (run) in runs:

            if isinstance( run, dict ) == 1:
                # in case of single process direct call.
                run_data = run['Data']
            else:
                run_data = runs[ run ]

            #pprint( run_data )

            for (time_key_original) in run_data:

                time_key = time_key_original
                yaxis_payload = run_data[ time_key_original ]

                for (between_str) in self.between_table:

                    enc = self.between_table[ between_str ]
                    #print( time_key_original )
                    time_key = time_key.replace( between_str, enc )
                    #print( time_key )

                compact_runs[ time_key ] = yaxis_payload

        return self.make_str_from_compact_runs( compact_runs )



    def make_str_from_compact_runs(self, compact_runs):

        compare_str = ""

        for (time_key) in compact_runs:

            payload = compact_runs[time_key]

            payload_str = str(payload)

            compare_str = compare_str + ',"' + time_key + '":' + payload_str

        #pprint( compare_str)
        return '"values":{' + compare_str[1:] + '}'


    def make_compare_str(self):

        import numpy as np

        runs = self.json_runs['Runs']
        #pprint(runs )
        runs_arr = []

        for (i) in runs:
            runs_arr.append( runs[i] )

        single_process = 0
        #  Single process works.
        if single_process == 1:

            compact_runs = self.subset_of_runs_handler( runs )
            return compact_runs

        else:
            #pprint( runs_arr )
            run_subsets = np.array_split( runs_arr, 18 )
            pool_res = multiprocessing.Pool(18).map( self.subset_of_runs_handler, run_subsets )

            pprint( len(pool_res) )
            #pprint( pool_res )
            compact_str = pool_res[2]
            #pprint(pool_res)
            #print('len=' + str(len(compact_str))) 
            #pprint( compact_str )
            return compact_str


    def render(self):

        table_str = self.make_table_str()
        compare_str = self.make_compare_str()

        return '{' + table_str + ',' + compare_str + '}'


