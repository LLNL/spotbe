from pprint import pprint
import glob, os, json

class CustomTemplates:

    def __init__(self):
        self.notebooks = []
        self.multi_notebooks = []

    def get(self, sf):
        try:
            self.get_files(sf)
        except Exception as e:
            print(e)

    def get_files(self, sf):

        self.check_home_dir()
        self.check_templates_dir()
        self.check_sf_dir( sf )

        combined = {}
        combined["single"] = self.notebooks
        combined["multi"] = self.multi_notebooks

        jnote = json.dumps( combined )

        pprint( jnote )
        return jnote


    def check_dir(self, check_dir, paste):

        if os.path.exists(check_dir) and os.path.isdir(check_dir):

            os.chdir(check_dir)

            for file in glob.glob("*.ipynb"):
                paste.append( check_dir + "/" + file)


    def check_sf_dir(self, sf):
        self.check_dir( sf + "/single", self.notebooks )
        self.check_dir( sf + "/multi", self.multi_notebooks )


    def check_templates_dir(self):

        temps_dir = "/usr/gapps/spot/templates/single"
        self.check_dir(temps_dir, self.notebooks)

        multi_dir = "/usr/gapps/spot/templates/multi"
        self.check_dir(multi_dir, self.multi_notebooks)


    def check_home_dir(self):

        from os.path import expanduser
        home = expanduser("~")        
        homedir = home + "/notebooks/single"

        self.check_dir(homedir, self.notebooks)

        multi_homedir = home + "/notebooks/multi"
        self.check_dir(multi_homedir, self.multi_notebooks)

