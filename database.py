import numpy as np
import sqlite3
import datetime



def insert_data1(c1,c2,totallapis,rows,current_time):
    conn = sqlite3.connect('/home/epiphany/yolov11_project/db_cam1')
    
    cursor = conn.cursor()
    # SQL query with placeholders
    sql_insert_query = """INSERT INTO infocam1 (timestamp, lapis1, lapis2, totallapis,rows) VALUES (  ?, ?, ?, ?, ?)"""

 
    data = (current_time, c1, c2,totallapis,rows)

    # Execute the query
    cursor.execute(sql_insert_query, data)
    conn.commit()
    cursor.close()
    conn.close()
def insert_data2(c1,c2,totallapis,rows,current_time):
    conn = sqlite3.connect('/home/epiphany/yolov11_project/db_cam1')

    
    cursor = conn.cursor()
    # SQL query with placeholders
    sql_insert_query = """INSERT INTO infocam2 (timestamp, lapis1, lapis2, totallapis,rows) VALUES (?,?, ?, ?, ?)"""

    # Data to insert (as a tuple)
    data = (current_time, c1, c2,totallapis,rows)

    # Execute the query
    cursor.execute(sql_insert_query, data)
    conn.commit()
    cursor.close()
    conn.close()
def insert_data3(variasi,jumlah,current_time):
    conn = sqlite3.connect('/home/epiphany/yolov11_project/db_cam1')
    # now = datetime.datetime.now()
    # current_time = now.strftime("%m/%d/%Y, %H:%M:%S")
    
    cursor = conn.cursor()
    # SQL query with placeholders
    sql_insert_query = """INSERT INTO inventory_data (timestamp, variasi, jumlah) VALUES (?,?,?)"""

    # Data to insert (as a tuple)
    data = (current_time,variasi,jumlah)

    # Execute the query
    cursor.execute(sql_insert_query, data)
    conn.commit()
    cursor.close()
    conn.close()
