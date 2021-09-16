from abc import ABC, abstractmethod

class SpotDB(ABC):
    """ SpotDB base class """
    
    @abstractmethod
    def get_global_metadata(self):
        """ Return a dict with metadata (e.g., data types) for all global 
            attributes found in the database.
        """
        pass

    @abstractmethod
    def get_metric_metadata(self):
        """ Return a dict with metadata (e.g., aliases) for all metric 
            attributes found in the database.
        """
        pass

    @abstractmethod
    def get_all_run_ids(self):
        """ Return a list with all run ids in the database 
        """
        pass

    @abstractmethod
    def get_new_runs(self, last_read_time):
        """ Return list of run ids newer than last_read """
        pass

    def get_global_data(self, run_ids):
        """ Return global attributes for the given list of run_ids

            Structure:

            { 
                run_id_1: { "attribute1": value1, "attribute2": value2, ... },
                run_id_2: { "attribute1": value1, "attribute2": value2, ... },
                ...
            } 
        """
        pass

    def get_regionprofiles(self, run_ids):
        """ Return region profile data for the given list of run ids 

            Structure:

            {
                run_id_1: 
                    { 
                        "main":     { "metric": val, ... }, 
                        "main/foo": { "metric": val, ... }, 
                        ... 
                    },
                run_id_2: { ... }, ...
            }
        """
        pass

    def get_channel_data(self, channel_name, run_ids):
        """ Return channel data (e.g., timeseries profile) for the 
            given list of run ids and channel 
        """
        pass

    # def query(self, query):
    #     """ Return list of run ids matching the given query """
    #     pass


def connect(database_key):
    """ Return a SpotDB object for the given database key 
        (directory or SQL connection string)
    """

    # if database_key is a directory:
    #    return spotcalidb.SpotCaliperDirectoryDB(database_key)
    # elif database_key is a SQL connection string:
    #    return spotsinadb.SpotSinaDB(database_key)
    # else:
    #    raise error

    pass
    