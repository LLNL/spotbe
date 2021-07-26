from pprint import pprint
import glob, os

class CustomTemplates:

    def __init__(self):
        self.notebooks = []
        x=5

    def get(self, sf):

        self.check_home_dir()
        self.check_templates_dir()
        self.check_sf_dir( sf )

        pprint( self.notebooks )
        return self.notebooks


    def check_sf_dir(self, sf):

        os.chdir(sf)
        for file in glob.glob("*.ipynb"):
            self.notebooks.append(file)


    def check_templates_dir(self):

        temps_dir = "/usr/gapps/spot/templates"
        os.chdir(temps_dir)

        for file in glob.glob("*.ipynb"):
            self.notebooks.append(file)


    def check_home_dir(self):

        from os.path import expanduser
        home = expanduser("~")        
        homedir = home + "/notebooks"

        if os.path.exists(homedir) and os.path.isdir(homedir):
            os.chdir(homedir)

            for file in glob.glob("*.ipynb"):
                self.notebooks.append(file)


