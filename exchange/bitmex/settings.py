# from os.path import join
import os
# from pathlib import Path,PurePath
import logging
import configparser

prj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir))
# prj_root = PurePath(os.path.abspath(os.path.join(__file__, os.pardir))).parents[3]
conf_path = os.path.join(prj_root,'config.ini')
settings = configparser.ConfigParser()
settings.read(conf_path)

# print(conf_path)