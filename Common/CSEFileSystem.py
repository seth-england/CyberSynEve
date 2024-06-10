import json
import CSELogging
import CSECommon
import os

def SplitFileAndExtension(file_path : str) -> (str, str):
  file_name = ""
  file_ex = ""
  dot_index = file_path.find('.')
  if dot_index != -1:
    file_name = file_path[0:dot_index]
    file_ex = file_path[dot_index:len(file_path)]
  else:
    file_name = file_path

  return (file_name, file_ex)

def WriteObjectJsonToFilePathHelper(file_path : str, json_string : str):
  try:
    with open(file_path, "w") as original_file:
      original_file.write(json_string)
  except FileNotFoundError:
    CSELogging.Log(f'{file_path} not found', __file__)
  except:
    CSECommon.Log(f'Failed to write {object} to {file_path}')

def WriteObjectJsonToFilePath(file_path : str, object : object):
  # serialize object to json string
  try:
    json_string = json.dumps(object, cls=CSECommon.GenericEncoder)
  except:
    CSECommon.Log(f'While writing to {file_path} could not serialize {object}')
    return

  file_name, file_ext = SplitFileAndExtension(file_path)

  WriteObjectJsonToFilePathHelper(file_path, json_string)
  WriteObjectJsonToFilePathHelper(file_name + CSECommon.BACKUP_FILE_SUFFIX + file_ext, json_string)

def ReadObjectFromFileJsonHelper(file_path : str) -> dict or None:
  try:
    with open(file_path, "r") as scrape_file:
      object_dict = json.load(scrape_file)
      return object_dict
  except FileNotFoundError as e:
    CSELogging.Log(f'LOAD FROM {file_path} FAILURE COULD NOT OPEN FILE', __file__)
  except EOFError:
    CSELogging.Log(f'LOAD FROM {file_path} FAILURE REACHED UNEXPECTED END OF FILE', __file__)
  except AttributeError:
    CSELogging.Log(f'LOAD FROM {file_path} FAILURE SCRAPE DEFINITION CHANGED', __file__)
  except json.JSONDecodeError:
    CSELogging.Log(f'LOAD FROM {file_path} FAILURE FAILED TO READ JSON', __file__)
  except UnicodeDecodeError:
    CSELogging.Log(f'LOAD FROM {file_path} FAILURE FAILED TO READ JSON', __file__)

  return None
  
def ReadObjectFromFileJson(file_path : str, dest_object : object):
  original_json_dict = ReadObjectFromFileJsonHelper(file_path)
  if original_json_dict:
    CSECommon.FromJson(dest_object, original_json_dict)
    return

  file_name, file_ext = SplitFileAndExtension(file_path)
  backup_0_file_path = file_name + CSECommon.BACKUP_FILE_SUFFIX + file_ext
  backup_0_json_dict = ReadObjectFromFileJsonHelper(backup_0_file_path)
  if backup_0_json_dict:
    CSECommon.FromJson(dest_object, backup_0_json_dict)
    return

def ReadObjectsFromDirectoryJson(directory_path : str, object_type):
  ret_val = list[object_type]()
  try:
    for file_name in os.listdir(directory_path):
      if file_name.find(f'{CSECommon.BACKUP_FILE_SUFFIX}.') >= 0:
        continue
      file_path = directory_path + file_name
      o = object_type()
      ReadObjectFromFileJson(file_path, o)
      ret_val.append(o)
  except FileNotFoundError:
    CSELogging.Log(f'LOAD FROM {directory_path} FAILURE COULD NOT OPEN DIRECTORY', __file__)
  return ret_val
  
