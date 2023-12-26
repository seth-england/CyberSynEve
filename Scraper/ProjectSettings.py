import sys
import os

ROOT_FOLDER = "C:/Projects/CyberSynEve"
ROOT_SETTINGS = "C:/Projects/CyberSynEve/ProjectSettings.py"

def Init():
  for directory in os.listdir(ROOT_FOLDER) :
    sub_dir = ROOT_FOLDER + '/' + directory + '/'
    if os.path.isdir(sub_dir) :     
      if not any(sys.path) is sub_dir :
        sys.path.append(sub_dir)