
import json, sys

class ErrorHandling:

        def __init__( self ):
            self.err = 5

        def output( self, error_message ):

            out = {
                "error": error_message,
                "output": "",
                "status": "ERROR"
            }

            return json.dump( out, sys.stdout )


        def check_file( self, filename ):

            from os.path import exists
            import os

            file_exists = exists( filename )
            have_permission = os.access( filename, os.R_OK)

            if not file_exists:

                error_message = "The input file: " + filename + " does not exist."
                return self.output( error_message )

            if not have_permission:
                error_message = "You do not have permission to read the input file: " + filename + "."
                return self.output( error_message )

            return True
