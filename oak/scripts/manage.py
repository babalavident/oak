#!/usr/bin/env python

import sys
import yaml
from oak.launcher import Launcher

if __name__ == '__main__':

    try:
        fd = open("settings.yaml")
        settings = yaml.load(fd.read())

    except Exception as e:
        print "Unable to load yaml settings file!"
        print "Exception: " + str(e)
        sys.exit(1)	
    
    launcher = Launcher(settings=settings)
    launcher.run(sys.argv[1:])

