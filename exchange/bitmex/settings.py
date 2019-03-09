# from os.path import join
import os
# from pathlib import Path,PurePath
import logging
import configparser
import sys
from .apihub.settings import prj_root
# prj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir))
# prj_root = PurePath(os.path.abspath(os.path.join(__file__, os.pardir))).parents[3]
# filename = sys.argv[0]
# dirname = os.path.dirname(filename)
# prj_root = os.path.abspath(dirname)
conf_path = os.path.join(prj_root,'config.ini')
settings = configparser.ConfigParser()
settings.read(conf_path)

# print(conf_path)