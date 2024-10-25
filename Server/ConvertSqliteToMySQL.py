import ProjectSettings
ProjectSettings.Init()
import MySQLHelpers
import SQLHelpers
import CSECommon
import SQLEntities

my_sql_conn = MySQLHelpers.Connect()
sql_lite_conn = SQLHelpers.Connect(CSECommon.MASTER_DB_PATH)

MySQLHelpers.CreateTable(my_sql_conn.cursor(), CSECommon.TABLE_CURRENT_ORDERS, SQLEntities.SQLOrder)
MySQLHelpers.CreateTable(my_sql_conn.cursor(), CSECommon.TABLE_SALE_RECORD, SQLEntities.SQLSaleRecord)

sql_lite_sale_record_cursor = sql_lite_conn.execute(f'SELECT * FROM {CSECommon.TABLE_SALE_RECORD}')
sale_records : list[SQLEntities.SQLSaleRecord] = SQLHelpers.ConstructInstancesFromCursor(sql_lite_sale_record_cursor, SQLEntities.SQLSaleRecord)

for sale_record in sale_records:
  MySQLHelpers.InsertOrUpdateInstanceInTable(my_sql_conn.cursor(), CSECommon.TABLE_SALE_RECORD, sale_record)

my_sql_conn.commit()
print("done")