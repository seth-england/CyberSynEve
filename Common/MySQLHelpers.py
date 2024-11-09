import mysql.connector.cursor
import CSECommon
import mysql.connector
import mysql.connector.abstracts
import inspect
import os
import datetime

Connection = mysql.connector.MySQLConnection
Cursor = mysql.connector.cursor.MySQLCursor

class EntityAttribute:
  def __init__(self, name : str, type : str, default_value):
    self.m_MemberName = name
    self.m_MemberType = type
    self.m_DefaultValue = default_value
    self.m_ActualValue = default_value

def Connect() -> Connection:
  conn = mysql.connector.connect(host=CSECommon.DB_URL, user='CSE', password='Dunayevskaya1!', database="Main", buffered=True)
  return conn

def TypeStringFromType(basic_type : type) -> str or None:
  if basic_type == int:
    return "BIGINT"
  elif basic_type == str:
    return "VARCHAR(255)"
  elif basic_type == float:
    return "DOUBLE"
  elif basic_type == datetime.datetime:
    return "DATETIME"
  elif basic_type == bool:
    return "TINYINT"
  else:
    return None

def EntityAttributes(entity_type) -> list[EntityAttribute]:
  result = list[EntityAttribute]()
  entity = entity_type()
  member_names = inspect.getmembers(entity)
  for member_name_tuple in member_names:
    member_name = member_name_tuple[0]
    value = getattr(entity, member_name)
    if member_name.startswith('__') or inspect.ismethod(value) or type(value) is type:
      continue
    type_string = TypeStringFromType(type(value))
    if type_string:
      result.append(EntityAttribute(member_name, type_string, value))
  return result

def EntityAttributeString(names : list[EntityAttribute]) -> str:
  result = ""
  count = len(names)
  primary_key = None
  for i, name in enumerate(names):
    result += f'{name.m_MemberName} {name.m_MemberType}'
    if name.m_MemberName == "m_ID":
      primary_key = name
    if i < (count - 1) or primary_key:
      result += ', '

  if primary_key:
    result += f'PRIMARY KEY ({primary_key.m_MemberName})'

  return result

def EntityAttributeNamesString(names : list[EntityAttribute]) -> str:
  result = ""
  count = len(names)
  for i, name in enumerate(names):
    result += f'{name.m_MemberName}'
    if i < (count - 1):
      result += ', '
  return result

def GetAttributeNamesFromTable(cursor : Cursor, table_name : str) -> list[str]:
  cursor.execute(f'select * from {table_name} LIMIT 1')
  names = [description[0] for description in cursor.description]
  return names

def InstanceValues(entity_instance) -> list[EntityAttribute]:
  res = EntityAttributes(type(entity_instance))
  member_names = inspect.getmembers(entity_instance)
  for member_name_tuple in member_names:
    member_name = member_name_tuple[0]
    matching_attribute = [attribute for attribute in res if attribute.m_MemberName == member_name]
    assert len(matching_attribute) < 2
    if len(matching_attribute) > 0:
      value = getattr(entity_instance, member_name)
      matching_attribute[0].m_ActualValue = value
  
  return res

def InstanceValueSet(values: list[EntityAttribute]):
  value_list = []
  for value in values:
    value_list.append(value.m_ActualValue)
  value_tuple = tuple(value_list)
  return value_tuple

def InstanceValuesString(values : list[EntityAttribute]):
  count = len(values)
  res = ''
  for i, value in enumerate(values):
    res += str(value.m_ActualValue)
    if i < (count - 1):
      res += ", "
  return res

def InstanceValuesPlaceholderString(values : list[EntityAttribute], names : bool = False):
  count = len(values)
  res = ''
  for i, value in enumerate(values):
    if names:
      res += f'{value.m_MemberName}=%s'
    else:
      res += '%s'
    if i < (count - 1):
      res += ", "
  return res

def InsertInstanceIntoTable(cursor : Cursor, table_name : str, entity_instance):
  entity_attributes = InstanceValues(entity_instance)
  attributes_string = EntityAttributeNamesString(entity_attributes)
  placeholder_string = InstanceValuesPlaceholderString(entity_attributes)
  instance_values_set = InstanceValueSet(entity_attributes)
  sql_string = f'INSERT INTO {table_name} ({attributes_string}) VALUES({placeholder_string})'
  cursor.execute(sql_string, instance_values_set)

def UpdateInstanceInTable(cursor : Cursor, table_name : str, entity_instance):
  entity_attributes = InstanceValues(entity_instance)
  placeholder_string = InstanceValuesPlaceholderString(entity_attributes, True)
  instance_values_set = InstanceValueSet(entity_attributes)
  values_set = (instance_values_set) + (entity_instance.m_ID,)
  sql_string = f'UPDATE {table_name} SET {placeholder_string} WHERE m_ID = %s'
  cursor.execute(sql_string, values_set)

def InsertOrUpdateInstanceInTable(cursor : Cursor, table_name : str, entity_instance):
  exists = DoesInstanceExistInTable(cursor, table_name, entity_instance.m_ID)
  if exists:
    UpdateInstanceInTable(cursor, table_name, entity_instance)
  else:
    InsertInstanceIntoTable(cursor, table_name, entity_instance)

def GetEntityById(cursor : Cursor, table_name : str, entity_type, id):
  cursor.execute(F'SELECT * FROM {table_name} WHERE m_ID = %s', (id,))
  results = ConstructInstancesFromCursor(cursor, entity_type)
  assert len(results) < 2
  if len(results) == 0:
    return None
  return results[0]

def ConstructInstancesFromCursor(cursor : Cursor, entity_type) -> list:
  result = list[entity_type]()
  rows = cursor.fetchall()
  for row in rows:
    name_value_pairs = [(description[0], value) for value, description in zip(row, cursor.description)]
    entity_instance = entity_type()
    for name, value in name_value_pairs:
      current_value = getattr(entity_instance, name)
      if current_value is not None:
        current_value_type = type(current_value)
        value_type = type(value)
        if current_value_type == datetime.datetime and value_type == str:
          try:
            value = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
          except:
            try:
              value = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except Exception as e:
              raise e
        elif current_value_type == bool:
          value = bool(value)
        elif current_value_type == str and value_type == int:
          value = str(value)
        setattr(entity_instance, name, value)
    result.append(entity_instance)
  return result


def DoesInstanceExistInTable(cursor : Cursor, table_name : str, id):
  cursor.execute(f'SELECT * FROM {table_name} WHERE m_ID = %s', (id,))
  rows = cursor.fetchall()
  assert len(rows) < 2
  if len(rows) == 0:
    return False
  else:
    return True

def CreateTable(cursor : Cursor, table_name : str, entity_type):
  try:
    attribute_names = EntityAttributes(entity_type)
    attributes_string = EntityAttributeString(attribute_names)
    sql_statement = f"CREATE TABLE IF NOT EXISTS {table_name} ({attributes_string})"
    cursor.execute(sql_statement)

    # Remove old columns
    existing_attr_names = GetAttributeNamesFromTable(cursor, table_name)
    for existing_attr_name in existing_attr_names:
      matching_names = [name for name in attribute_names if name.m_MemberName == existing_attr_name]
      assert len(matching_names) < 2
      # Column does not exist remove it
      if len(matching_names) == 0:
        cursor.execute(f'ALTER TABLE {table_name} DROP COLUMN {existing_attr_name}')

    # Add new columns
    for new_attr_name in attribute_names:
      matching_names = [name for name in existing_attr_names if name == new_attr_name.m_MemberName]
      assert len(matching_names) < 2
      if len(matching_names) == 0:
        cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {new_attr_name.m_MemberName} {new_attr_name.m_MemberType}')

  except mysql.connector.Error as e:
    print(e)