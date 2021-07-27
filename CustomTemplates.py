from pprint import pprint
import glob, os, json

class CustomTemplates:

    def __init__(self):
        self.notebooks = []
        self.multi_notebooks = []

    def get(self, sf):

        self.check_home_dir()
        self.check_templates_dir()
        self.check_sf_dir( sf )

        jnote = json.dumps( self.notebooks )

        pprint( jnote )
        return jnote


    def check_dir(self, check_dir, paste):

        if os.path.exists(check_dir) and os.path.isdir(check_dir):

            os.chdir(check_dir)

            for file in glob.glob("*.ipynb"):
                paste.append( check_dir + "/" + file)


    def check_sf_dir(self, sf):
        self.check_dir( sf, self.notebooks )


    def check_templates_dir(self):

        temps_dir = "/usr/gapps/spot/templates"
        self.check_dir(temps_dir, self.notebooks)


    def check_home_dir(self):

        from os.path import expanduser
        home = expanduser("~")        
        homedir = home + "/notebooks"

        self.check_dir(homedir, self.notebooks)

        multi_homedir = home + "/multi_notebooks"

