from os.path import join
import os
from pathlib import Path,PurePath
import logging
import configparser

prj_root = PurePath(os.path.abspath(__file__)).parents[3]
cong_path = PurePath(prj_root,'config.ini')
settings = configparser.ConfigParser()
settings.read(cong_path)

