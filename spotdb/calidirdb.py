from spotdb.spotdb import SpotDB

class SpotCaliperDirectoryDB(SpotDB):
    """ Access Spot data from a directory with Caliper files
    """

    def __init__(self, dirname):
        self.directory = dirname
    

    def get_global_metadata(self):
        return super().get_global_metadata()
    

    def get_metric_metadata(self):
        return super().get_metric_metadata()

    
    def get_all_run_ids(self):
        return super().get_all_run_ids()


    def get_new_runs(self, last_read_time):
        return super().get_new_runs(last_read_time)

        
    def get_regionprofiles(self, run_ids):
        return super().get_regionprofiles(run_ids)
    

    def get_channel_data(self, channel_name, run_ids):
        return super().get_channel_data(channel_name, run_ids)