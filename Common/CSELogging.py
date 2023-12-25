import time

from datetime import datetime
import os

def Log(message = "", file = __file__):
    current_date_time = datetime.now()
    current_date_time_string = current_date_time.strftime("%H:%M:%S")
    current_date_time_string = f'{current_date_time_string}:{current_date_time.microsecond}'
    base_file = os.path.basename(file)
    log_str = print(f'{base_file} {current_date_time_string}: {message}')