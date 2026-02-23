import numpy as np
import sqlite3

def read(database_file):
    conn = None
    try:
        conn = sqlite3.connect(database_file)
        cur = conn.cursor()
        cur.execute("SELECT * FROM infocam1 ORDER BY ROWID DESC LIMIT 1")
        c1 = cur.fetchone()
        cur.execute("SELECT * FROM infocam2 ORDER BY ROWID DESC LIMIT 1")
        c2 = cur.fetchone()
        
  
        cam1=(c1[1],c1[2])
        cam2=(c2[1],c2[2]) 
        return cam1,cam2

    except sqlite3.Error as e:
        print(f"A database error occurred: {e}")
    finally:
        if conn:
            conn.close()
def hitung(C1L1,C1L2,C2L1,C2L2,total):
    # 1 baris saja pasti variasi 1
    if((C1L1==1 or C2L1==1)  and (C1L1==2 or C2L1==2)):
        print("variasi 1 hitung dr kamera yg detek 1 lapis SAJA")
        return total
    #variasi 2 -> 2,1 // 2,2
    if((((C1L1==2 and C1L2==1) or (C1L1==1 and C1L2==2)) and ((C2L1==2 and C2L2==2))) or (((C2L1==2 and C2L2==1) or (C2L1==1 and C2L2==2)) and ((C1L1==2 and C1L2==2))) ) :
        print("variasi 2 ")
        return total
    #variasi 3 -> 2,3 // 2,2
    if(((C1L1==2 and C1L2==2) and (C2L1==3 and C2L2==2 or C2L1==2 and C2L2==3 )) or ((C2L1==2 and C2L2==2) and (C1L1==3 and C1L2==2 or C1L1==2 and C1L2==3 ))  ) :
        pass
    #variasi 4 -> 3,2 // 3,3
    if((C1L1==3 and C2L1==3) or (C2L2==3 and C2L2==3)):
        pass
    #variasi 5 -> 2,2 // 2,2
    if(C1L1==C1L2==2 and C2L1==C2L2==2):
        hasil='x'
        return  hasil
    

  
# hasil_cam1, hasil_cam2 = read('db_cam1')
# print(hasil_cam1[0])