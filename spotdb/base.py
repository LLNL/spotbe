from abc import ABC, abstractmethod

class SpotDB(ABC):
    """ SpotDB base class """

    @abstractmethod
    def get_all_run_data(self, last_read_time):
        """ Return a dict with region profile and global values for each
            run in the database that is newer than last_read_time 
        """
        pass

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

    def get_global_data(self, run_id):
        """ Get global attributes for the given run_id """
        pass

    def get_regionprofile(self, run_id):
        """ Return region profile data for the given run id """
        pass

    def get_channel_data(self, channel_name, run_id):
        """ Return channel data (e.g., timeseries profile) for the 
            given run id and channel 
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
    # else if database_key is a SQL connection string:
    #    return spotsinadb.SpotSinaDB(database_key)
    # else:
    #    raise error

    pass
    