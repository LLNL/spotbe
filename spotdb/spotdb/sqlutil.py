import configparser

def make_sql_uri_from_cnf(filename):
    """Construct a MySQL DB URI from a MySQL .cnf file
    """

    parser = configparser.ConfigParser(allow_no_value=True)
    parser.read(filename)

    config = parser["client"] if "client" in parser else parser

    args = []

    # Needed for LLNL spotdb config
    if "ssl_verify_cert" not in config:
        args.append("ssl_verify_cert=false")
    
    args.append("read_default_file=" + filename)

    uri  = "mysql+pymysql://" + config["host"] + "/"
    if (len(args) > 0):
        uri += "?" + "&".join(args)

    return uri
