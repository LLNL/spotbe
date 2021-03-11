
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


    def subset_of_runs_handler(self, run_data):

        import json
        compact_runs = {}

        #print( "run data:" )
        #pprint( run_data )

        ret_str = ""

        for (global_data_rk_obj) in run_data:

            # run_key looks like: "generator/3d_ex0"
            run_key = global_data_rk_obj['rk']

            # remove the run key because it was only added to pass the run_key to this function.
            global_data_rk_obj.pop('rk', None)

            dict_compressed_gdr_obj = self.replace_dictionary_strs( global_data_rk_obj )

            ret_str = ret_str + ',"' + run_key + '":' + json.dumps( dict_compressed_gdr_obj )

        return ret_str[1:]


    def replace_dictionary_strs( self, global_data_rk_obj ):

        dict_compressed_gdr_obj = {}
        Data = global_data_rk_obj['Data']

        for (long_generator_str) in Data:

            yAxis_payload = Data[long_generator_str]

            for (between_str) in self.between_table:

                enc = self.between_table[ between_str ]
                compressed_gen_str = long_generator_str.replace( between_str, enc )

            dict_compressed_gdr_obj[ compressed_gen_str ] = yAxis_payload

        pprint( dict_compressed_gdr_obj )
        return dict_compressed_gdr_obj


    def make_str_from_compact_runs(self, compact_runs):

        compare_str = ""

        for (time_key) in compact_runs:

            payload = compact_runs[time_key]

            payload_str = str(payload)

            compare_str = compare_str + ',"' + time_key + '":' + payload_str

        return '"values":{' + compare_str[1:] + '}'


    def make_compare_str(self):

        import numpy as np

        runs = self.json_runs['Runs']
        runs_arr = []

        for (i) in runs:
            runs[i]['rk'] = i
            runs_arr.append( runs[i] )

        single_process = 0
        #  Single process works.
        if single_process == 1:

            compact_runs = self.subset_of_runs_handler( runs )
            return compact_runs

        else:
            #print( "runs_arr: ")
            #pprint( runs_arr )
            run_subsets = self.split_workload( runs_arr, 5 )
            #pprint( run_subsets )
            #exit()
            pool_res = multiprocessing.Pool(5).map( self.subset_of_runs_handler, run_subsets )

            #print("Pool results:")
            #pprint( len(pool_res) )
            #pprint( pool_res )
            pool_str = ",".join( pool_res )
            return '"Pool":{' + pool_str + '}'


    def split_workload( self, runs_arr, split_count ):

        import numpy as np

        run_subsets = np.array_split( runs_arr, split_count )

        return run_subsets


    #  Each pool result just contains the "ad/av/bx": {'yaAxis': 0.002} for it's pool execution
    def collect_and_render_pool_results( self, pool_res ):

        str_sum = ""

        for (i) in pool_res:
            str_sum = str_sum + pool_res[i]

        return str_sum


    def render(self):

        table_str = self.make_table_str()
        compare_str = self.make_compare_str()

        json_str = '{' + table_str + ',' + compare_str + '}'

        import json
        try:
            json.loads(json_str)
        except ValueError as error:
            print("invalid json: %s" % error)
            return False

        return json_str


