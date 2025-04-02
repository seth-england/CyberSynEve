import os
import sys

ROOT_FOLDER = os.path.dirname(os.path.abspath(__file__))
ROOT_SETTINGS_TEMPLATE = f'{ROOT_FOLDER}\\ProjectSettingsTemplate.py'

root_file = open(ROOT_SETTINGS_TEMPLATE, 'r')
root_settings_string = root_file.read()
root_settings_string = root_settings_string.replace("ROOT_FOLDER", f'ROOT_FOLDER=\"{ROOT_FOLDER.replace("\\","/")}\"', 1)
for directory in os.listdir(ROOT_FOLDER) :
  if os.path.isdir(directory) :
    file_path = ROOT_FOLDER + '/' + directory + '/' + 'ProjectSettings.py'
    if os.path.exists(file_path):
      os.remove(file_path)
    new_file = open(file_path, 'w')
    new_file.write(root_settings_string)
    new_file.close()
    root_file.close()