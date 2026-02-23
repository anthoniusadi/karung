import numpy as np
import sqlite3
import datetime



def insert_data(c1,c2,var,totallapis,jumlah):
    conn = sqlite3.connect('/home/epiphany/yolov11_project/db_cam1')
    now = datetime.datetime.now()
    current_time = now.strftime("%m/%d/%Y, %H:%M:%S")
    
    cursor = conn.cursor()
    # SQL query with placeholders
    #sql_insert_query = """INSERT INTO infocam1 (timestamp, lapis1, lapis2, variasi, totallapis, jumlah) VALUES (?, ?, ?, ?, ?, ?)"""
    sql_insert_query = """INSERT INTO infocam2 (timestamp, lapis1, lapis2, variasi, totallapis, jumlah) VALUES (?, ?, ?, ?, ?, ?)"""

    # Data to insert (as a tuple)
    data = (current_time, c1, c2,var,totallapis,jumlah)

    # Execute the query
    cursor.execute(sql_insert_query, data)
    conn.commit()
    cursor.close()
    conn.close()
