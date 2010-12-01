# -*- coding: utf-8 -*-

import sys
import os
import logging
logger = logging.getLogger("oak")

from optparse import OptionParser, OptionGroup

import oak

class Launcher(object):
    "The entrypoint for command line calls"

    LOG_LEVELS = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }

    settings = None

    def __init__(self, settings):
        self.settings = settings

    def setup_logging(self, loglevel='warning'):
        # self.logger = logging.getLogger('oak')

        ch = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(asctime)s:%(name)s:%(levelname)s:%(message)s")
        ch.setFormatter(formatter)
        ch.setLevel(self.LOG_LEVELS[loglevel])
        logger.addHandler(ch)
        logger.setLevel(self.LOG_LEVELS[loglevel])

    def run(self, argv=None):
        parser = OptionParser(usage="%prog [OPTIONS]", version="%prog 0.1")
        parser.add_option("-g", "--generate", action="store_true", dest="generate", default=False, help = "Generate the source for your site.")
        parser.add_option("--loglevel", dest="loglevel", default="warning", help="Set the log output level")

        group = OptionGroup(parser, "Output options (overriding settings.py)")
        group.add_option("-l", "--layout", dest="layout", help="Set the layout to use")
        group.add_option("-d", "--destination", dest="destination", help="Set the destination of the output")
        parser.add_option_group(group)

        (options, args) = parser.parse_args()
        print(options.loglevel)

        self.setup_logging(loglevel=options.loglevel)

        if options.generate:

            # override settings with commandline options
            if options.layout:
                self.settings['blog']['default_layout']=options.layout
            if options.destination:
                self.settings['physical_paths']['output']=options.destination

            # set the path to the layouts directory, if LAYOUTS_PATH is not absolute, use the layouts from the package
            # TODO test!
            if not os.path.isabs(self.settings['physical_paths']['layouts']):
                self.settings['physical_paths']['layouts'] = os.path.sep.join([os.path.dirname(oak.__file__), self.settings['physical_paths']['layouts']])
            logger.debug("LAYOUTS_PATH set to %s" % (self.settings['physical_paths']['layouts'],))
            logger.info("Settings loaded.")
            # instantiate Oak with the given settings

            my_oak = oak.Oak(settings=self.settings)
            logger.info("Oak initiated.")
            # call the generation process
            my_oak.generate()
            logger.info("Generation completed.")
        else:
            parser.print_help()

