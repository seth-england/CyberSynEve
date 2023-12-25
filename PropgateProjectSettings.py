import ProjectSettings
import os
import sys

root_file = open(ProjectSettings.ROOT_SETTINGS, 'r')
root_settings_string = root_file.read()
for directory in os.listdir(ProjectSettings.ROOT_FOLDER) :
  if os.path.isdir(directory) :
    file_path = ProjectSettings.ROOT_FOLDER + '/' + directory + '/' + 'ProjectSettings.py'
    if os.path.exists(file_path):
      os.remove(file_path)
    new_file = open(file_path, 'w')
    new_file.write(root_settings_string)
    new_file.close()
    root_file.close()