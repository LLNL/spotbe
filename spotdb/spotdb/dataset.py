class StringCache:
    """ Maintains a list of common strings
    """

    def __init__(self):
        self.strings = []

    def get_or_insert(self, s):
        """ Return ID for string s. Inserts s if it does not exist yet.
        """

        if s in self.strings:
            return self.strings.index(s)
        else:
            self.strings.append(s)
            return len(self.strings)


class ProfileDataset:
    """ A SPOT profile dataset, containing profile data for a set of runs 
    """

    def __init__(self, column_info):
        self.columns = list(column_info.keys())
        self.column_metadata = column_info
        self.strings = StringCache()
        self.dataset = {}


    def add(self, run, records):
        def _val(column, record):
            if column not in record:
                return None
            if self.column_metadata[column].get("is_value", False) == False:
                return self.strings.get_or_insert(record[column])
            else:
                return record[column]

        data = []

        for rec in records:
            data.append( [ _val(c, rec) for c in self.columns ] )
        
        self.dataset[run] = data


    def get_object(self):
        return { 
            "columns":         self.columns,
            "column_metadata": self.column_metadata, 
            "dataset":         self.dataset,
            "strings":         self.strings.strings
        }
