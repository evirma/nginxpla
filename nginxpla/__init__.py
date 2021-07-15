__version__ = '0.0.6'
__aka__ = 'Nginx Python Log Analyser'

import os
import sys

VERSION = "{} <{}> v{}".format(__name__, __aka__, __version__)

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

HOME = os.path.expanduser("~/.nginxpla")
CUSTOM_MODULES_DIR = os.path.expanduser("~/.nginxpla/module")
CONFIG_FILE = HOME + '/nginxpla.yaml'

sys.path.append(os.path.dirname(CUSTOM_MODULES_DIR))
