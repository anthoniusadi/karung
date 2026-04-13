import cv2
import numpy as np
import time
from ultralytics import YOLO
from collections import defaultdict
import random
import statistics
import os
import module_menghitung_lapisan
import shutil
from datetime import datetime
import database
from preprocessing import sharpen_image


count=random.randint(1,400)
# --- 1. Konfigurasi ---
# panggin di raspi
# WEIGHTS_PATH = 'ncnn/final_ncnn_model' 
WEIGHTS_PATH = 'ncnn/final.pt' 
VIDEO_PATH1 = 'dataapril/samping/v7_1.mp4'    
VIDEO_PATH2 = 'dataapril/depan/v7_1.mp4' 


CONF_THRES = 0.5
IOU_THRES = 0.45
CLASS_NAMES = ['karung'] 
folder_path = 'temp_file/'
#  Garis Vertikal
LINE_POSITION_NONE = 0.25
LINE_POSITION_RATIO_A = 0.50
LINE_POSITION_RATIO_B = 0.80
LINE_Y_START = 100
LINE_COLOR = (190, 20, 15)
LINE_THICKNESS = 2

# Konfigurasi Area Tengah
CENTER_AREA_NONE = 0.15
CENTER_AREA_START_RATIO = 0.50
CENTER_AREA_END_RATIO = 0.80

# --- 2. Inisialisasi Model & State ---
model = YOLO(WEIGHTS_PATH)

# State untuk Logika Crossing
object_states = defaultdict(str) 
previous_centroids = {} 
total_count_L_to_R = 0
total_count_R_to_L = 0

# --- 3. load Video ---
cap = cv2.VideoCapture(VIDEO_PATH2)
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

# Output Video
#out = cv2.VideoWriter('ujicoba/output_video_'+str(count)+'.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 20, (frame_width, frame_height))

# Perhitungan Garis
column_x_a = int(frame_height * LINE_POSITION_RATIO_A)
column_x_b = int(frame_height * LINE_POSITION_RATIO_B)
column_x_x = int(frame_height * LINE_POSITION_NONE)

CENTER_AREA_NONE = int(frame_height * CENTER_AREA_NONE)
CENTER_AREA_START_Y = int(frame_height * CENTER_AREA_START_RATIO)
CENTER_AREA_END_Y = int(frame_height * CENTER_AREA_END_RATIO)
temp=[]
pola={0,0,0}
def check(arah):
    if arah=={1,2,3}:
        # print("hitung")
        return False
    if arah=={3,2,1}:
        # print("tidak hitung")
        return True
    else:
        # print(f"waitt..{arah}")
        return None
def hapus_tempfile(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path) 
                # print(f"hapus file: {filename}")
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path) 
                # print(f"hapus directory: {filename}")
        except Exception as e:
            print(f'Failed to delete {file_path}. {e}')
# --- 4. Proses Frame ---
modus=[]
num=0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break
    
    # frame[0:CENTER_AREA_NONE, :] = [0, 0, 255]
    original_frame = frame.copy()

    # Inferensi
    # persist=True penting jika ingin menggunakan tracker bawaan (id)
    results = model.track(frame, persist=True, conf=CONF_THRES, iou=IOU_THRES, verbose=False)
    # Gambar Garis Panduan
    cv2.line(frame, (0, column_x_x), (frame_width,column_x_x ), (200,200, 210), 1)
    
    cv2.line(frame, (0, column_x_a), (frame_width,column_x_a ), (0,255, 0), 1)
    cv2.line(frame, (0, column_x_b, ), (frame_width, column_x_b), (0, 0, 255), 1)
    # cv2.line(frame, (50,100), (600,100 ), (255, 0, 0), 1)#bgr red
    # cv2.line(frame, (50,200), (600,200 ), (0, 0, 255), 1)#bgr red
    # cv2.line(frame, (50,350), (600, 350), (0, 255, 0), 1)#green
    frame_centroids = []
    current_ids = []

    if results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        ids = results[0].boxes.id.int().cpu().numpy()
        confs = results[0].boxes.conf.cpu().numpy()
        clss = results[0].boxes.cls.int().cpu().numpy()

        for box, obj_id, conf, cls in zip(boxes, ids, confs, clss):
            x1, y1, x2, y2 = map(int, box)
            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
            
            frame_centroids.append((center_x, center_y))
            current_ids.append(obj_id)

            # --- LOGIKA CROSSING (State Machine) ---
            state_old = object_states[obj_id]
            center_x_old = previous_centroids.get(obj_id)
            
            if column_x_a < center_x < column_x_b:
                object_states[obj_id] = 'BETWEEN'

            if center_x_old is not None:
                if state_old == 'START_L' and center_x > column_x_b:
                    total_count_L_to_R += 1
                    object_states[obj_id] = 'COUNTED'
                    print("kanaaan")
                elif state_old == 'START_R' and center_x < column_x_a:
                    total_count_R_to_L += 1
                    object_states[obj_id] = 'COUNTED'
                    print("kiiiiirriiii")
                    

            if center_x < column_x_a and state_old not in ['START_L', 'COUNTED']:
                object_states[obj_id] = 'START_L'
                
            elif center_x > column_x_b and state_old not in ['START_R', 'COUNTED']:
                object_states[obj_id] = 'START_R'
                

            previous_centroids[obj_id] = center_x
            
            # Visualisasi Box
            label = f'ID:{obj_id} {object_states[obj_id]} {conf:.2f}'
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # --- GLOBAL CENTROID ---
    # print(frame_centroids)
    if frame_centroids:
        all_x = [c[0] for c in frame_centroids]
        all_y = [c[1] for c in frame_centroids]
        global_center_x, global_center_y = int(np.mean(all_x)), int(np.mean(all_y))

        if CENTER_AREA_START_Y <= global_center_y <= CENTER_AREA_END_Y:
            status_text = "STATUS:  TENGAH"
            color = (0, 0, 255)
            cv2.putText(frame, f'Sisi: {len(frame_centroids)}', (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1)
            cv2.putText(frame, f'Est. Total: {len(frame_centroids)*2}', (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1)
            kondisi=0
            temp.append(0)
            #print(f"capture!{len(frame_centroids)}")
            modus.append(len(frame_centroids))
            now = datetime.now()

            filename='temp_file/'+str(now.strftime("%d %B %Y %H:%M:%S_"))+str(num)+'.jpg'
        
            # filename='temp_file/temp_image_'+str(num)+'.jpg'
            
            cv2.imwrite(filename,original_frame)
            num+=1
            
        elif global_center_y <= CENTER_AREA_NONE:   
            status_text = "Area None"
            color = (0,0,255)
            # temp=[]
            
        elif global_center_y > CENTER_AREA_END_Y:
            status_text = "STATUS: zona C"
            color = (255, 0, 0)
            kondisi = 3
            temp.append(3)
        elif CENTER_AREA_NONE< global_center_y < CENTER_AREA_START_Y :
            status_text = "STATUS: zona A"
            color = (0, 255,0)
            kondisi = 1
            temp.append(1)
        cv2.circle(frame, (global_center_x, global_center_y), 10, color, -1)
        cv2.putText(frame, status_text, (50, frame_height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 1)
        #tmp = check(pola)
    else:
        cv2.putText(frame, 'none', (50, frame_height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 255), 1)
        # print(f'TOTAL : {temp}')
        res = []
        num=0

        for item in temp:
            if item not in res:
                res.append(item)
        temp=[]
        # print(f'result : {res}')
        if res==[1,0,3]:
            # print("hitung")
            # print(statistics.mode(modus))
            time.sleep(3)
            modus=[]
            num=0
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                # if(file_path[-7:]=='_28.jpg') and state:
                if(file_path[-6:]=='_3.jpg') and state:
                    
                    result=sharpen_image(file_path)
                    cv2.imwrite(file_path, result)
                    
                    
                    _,row2=module_menghitung_lapisan.lapisan(file_path,caminfo=2)
                    shutil.move(file_path,'folder_foto/')
                    state= False
            hapus_tempfile(folder_path)
            state = True
            time.sleep(3)
            
            cap.release()
            cv2.destroyAllWindows()

        elif res==[3,0,1]:
            # print("tidak hitung")
            hapus_tempfile(folder_path)
            time.sleep(3)
    state = True   
    # Pembersihan 
    for oid in list(previous_centroids.keys()):
        if oid not in current_ids:
            previous_centroids.pop(oid, None)
            object_states.pop(oid, None)

    cv2.imshow('Karung Tracking', frame)
    #out.write(frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
#out.release()
cv2.destroyAllWindows()

import count_karung
import jsonfile
import gpt
count=random.randint(1,400)
# - Konfigurasi ---
#WEIGHTS_PATH = 'ncnn/alldataset.pt' 
# maret dataset
# WEIGHTS_PATH = 'ds/best.pt' 


 

# Konfigurasi Garis Vertikal
LINE_POSITION_RATIO_R = 0.90
LINE_POSITION_RATIO_L = 0.20
LINE_Y_START = 70
LINE_COLOR = (190, 20, 15)
LINE_THICKNESS = 2

# Konfigurasi Area Tengah
CENTER_AREA_START_RATIO = 0.40
CENTER_AREA_END_RATIO = 0.60

model = YOLO(WEIGHTS_PATH)

object_states = defaultdict(str) 
previous_centroids = {} 
total_count_L_to_R = 0
total_count_R_to_L = 0

cap = cv2.VideoCapture(VIDEO_PATH1)
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

# Perhitungan Garis
column_x_r = int(frame_width * LINE_POSITION_RATIO_R)
column_x_l = int(frame_width * LINE_POSITION_RATIO_L)
CENTER_AREA_START_X = int(frame_width * CENTER_AREA_START_RATIO)
CENTER_AREA_END_X = int(frame_width * CENTER_AREA_END_RATIO)
temp=[]
pola={0,0,0}
def hapus_tempfile(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path) 
                # print(f"hapus file: {filename}")
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path) 
                # print(f"hapus directory: {filename}")
        except Exception as e:
            print(f'Failed to delete {file_path}. {e}')
def check(arah):
    if arah=={1,2,3}:
        # print("tdk hitung")
        return False
    if arah=={3,2,1}:
        # print("hitung")
        return True
    else:
        print(f"waitt..{arah}")
        return None
# ---  Proses Frame ---
modus=[]
num=0
folder_path = 'temp_file/'
while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break
    original = frame.copy()
    
#kalau gagal persist = False
    results = model.track(frame, persist=True, conf=CONF_THRES, iou=IOU_THRES, verbose=False)
    
    cv2.line(frame, (column_x_l, LINE_Y_START), (column_x_l, frame_height), LINE_COLOR, LINE_THICKNESS)
    cv2.line(frame, (column_x_r, LINE_Y_START), (column_x_r, frame_height), LINE_COLOR, LINE_THICKNESS)
    cv2.line(frame, (CENTER_AREA_START_X, LINE_Y_START), (CENTER_AREA_START_X, frame_height), (0, 255, 0), 1)
    cv2.line(frame, (CENTER_AREA_END_X, LINE_Y_START), (CENTER_AREA_END_X, frame_height), (0, 255, 0), 1)

    frame_centroids = []
    current_ids = []

    if results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        ids = results[0].boxes.id.int().cpu().numpy()
        confs = results[0].boxes.conf.cpu().numpy()
        clss = results[0].boxes.cls.int().cpu().numpy()

        for box, obj_id, conf, cls in zip(boxes, ids, confs, clss):
            x1, y1, x2, y2 = map(int, box)
            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
            
            frame_centroids.append((center_x, center_y))
            current_ids.append(obj_id)

            ### --- LOGIKA CROSSING untuk arah---###
            state_old = object_states[obj_id]
            center_x_old = previous_centroids.get(obj_id)
            
            if column_x_l < center_x < column_x_r:
                object_states[obj_id] = 'BETWEEN'

            if center_x_old is not None:
                if state_old == 'START_L' and center_x > column_x_r:
                    total_count_L_to_R += 1
                    object_states[obj_id] = 'COUNTED'
                    print("kanaaan")
                elif state_old == 'START_R' and center_x < column_x_l:
                    total_count_R_to_L += 1
                    object_states[obj_id] = 'COUNTED'
                    print("kiiiiirriiii")
                    

            if center_x < column_x_l and state_old not in ['START_L', 'COUNTED']:
                object_states[obj_id] = 'START_L'
                
            elif center_x > column_x_r and state_old not in ['START_R', 'COUNTED']:
                object_states[obj_id] = 'START_R'
                

            previous_centroids[obj_id] = center_x
            
            ##### Visualisasi Box
            label = f'ID:{obj_id} {object_states[obj_id]} {conf:.2f}'
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    ############ --- GLOBAL CENTROID ---
    if frame_centroids:
        all_x = [c[0] for c in frame_centroids]
        all_y = [c[1] for c in frame_centroids]
        global_center_x, global_center_y = int(np.mean(all_x)), int(np.mean(all_y))
        

        if CENTER_AREA_START_X <= global_center_x <= CENTER_AREA_END_X:
            status_text = "STATUS:  TENGAH"
            color = (0, 0, 255)
            cv2.putText(frame, f'Sisi: {len(frame_centroids)}', (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1)
            cv2.putText(frame, f'Total: {len(frame_centroids)*2}', (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1)
            kondisi=0
            temp.append(0)
            # print(f"capture!{len(frame_centroids)}")
            modus.append(len(frame_centroids))
            now = datetime.now()

            filename='temp_file/'+str(now.strftime("%d %B %Y %H:%M:%S_"))+str(num)+'.jpg'
        
            cv2.imwrite(filename,original)
            num+=1
            
        elif global_center_x > CENTER_AREA_END_X:
            status_text = "STATUS: kanan"
            color = (255, 0, 0)
            kondisi = 3
            temp.append(3)
        elif global_center_x < CENTER_AREA_START_X :
            status_text = "STATUS: kiri"
            color = (0, 255,0)
            kondisi = 1
            temp.append(1)
        cv2.circle(frame, (global_center_x, global_center_y), 10, color, -1)
        cv2.putText(frame, status_text, (50, frame_height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 1)
        #tmp = check(pola)
    else:
        cv2.putText(frame, 'none', (50, frame_height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 255), 1)
        # print(f'TOTAL : {temp}')
        res = []
        num=0

        for item in temp:
            if item not in res:
                res.append(item)
        temp=[]
        # print(f'result : {res}')
        if res==[3,0,1]:
            # print("hitung")
            # print(statistics.mode(modus))
            time.sleep(1)
            
            modus=[]
            num = 0
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if(file_path[-6:]=='_3.jpg') and state:
                    _,row1=module_menghitung_lapisan.lapisan(file_path,caminfo=1)
                    shutil.move(file_path,'folder_foto/')
                    state= False
                    """
                    request: lapis_raspi2,row2 = lapisan()
                    lapis_raspi1,row1 = lapisan()
                    
                    
                    hasil = hitung(C1L1,C1L2,C2L1,C2L2,row1,row2):
                    atau pakai
                    hitung(row1,row2)
                    
                    add database -> hasil
                    """
                    # nunggu json
                    # hitung karung
                    # add database
            hapus_tempfile(folder_path)

            cap.release()
            cv2.destroyAllWindows()
        elif res==[1,0,3]:
            # print("tidak hitung")
            hapus_tempfile(folder_path)
            
            time.sleep(1)
    state = True
    # Pembersihan State
    for oid in list(previous_centroids.keys()):
        if oid not in current_ids:
            previous_centroids.pop(oid, None)
            object_states.pop(oid, None)

    cv2.imshow('kamera', frame)
    #out.write(frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
#out.release()
cv2.destroyAllWindows()

# cam1,cam2=count_karung.read()


# row1 = jsonfile.load_json_sqlite(cam1[3])
# row2 = jsonfile.load_json_sqlite(cam2[3])

# print(int(len(row1[-1])),int(len(row1[-2])),int(len(row2[-1])),int(len(row2[-2])))
# final=count_karung.hitung(cam1[0],cam1[1],cam2[0],cam2[1],row1,row2)
final,variasi=count_karung.hitung(int(len(row1[-1])),int(len(row1[-2])),int(len(row2[-1])),int(len(row2[-2])),row1,row2)
print(f'===== ===== ===== ==== ===== =====')
print(f'===== HASIL DETEKSI KARUNG {final} =====')
print(f'===== ===== ===== ==== ===== =====')
now = datetime.now()
current_time = now.strftime("%m/%d/%Y, %H:%M:%S")
database.insert_data1(int(len(row1[-1])),  int(len(row1[-2])),  int(len(row1)),  'row1',  current_time)
database.insert_data2(int(len(row2[-1])),  int(len(row2[-2])),  int(len(row1)),  'row2',  current_time)
database.insert_data3(variasi,final,current_time)

