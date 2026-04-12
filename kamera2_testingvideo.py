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

# WEIGHTS_PATH = 'ds/best.pt' 
WEIGHTS_PATH = 'ncnn/final.pt' 

VIDEO_PATH = 'dataapril/depan/variasi4.mp4' 
CONF_THRES = 0.45
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
cap = cv2.VideoCapture(VIDEO_PATH)
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

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
        print("hitung")
        return False
    if arah=={3,2,1}:
        print("tidak hitung")
        return True
    else:
        print(f"waitt..{arah}")
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
    results = model.track(frame, persist=False, conf=CONF_THRES, iou=IOU_THRES, verbose=False)
    # Gambar Garis Panduan
    cv2.line(frame, (0, column_x_x), (frame_width,column_x_x ), (200,200, 210), 1)
    cv2.line(frame, (0, column_x_a), (frame_width,column_x_a ), (0,255, 0), 1)
    cv2.line(frame, (0, column_x_b, ), (frame_width, column_x_b), (0, 0, 255), 1)

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
            print("hitung")
            print(statistics.mode(modus))
            time.sleep(3)
            modus=[]
            num=0
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if(file_path[-6:]=='_7.jpg') and state:
                    result=sharpen_image(file_path)
                    cv2.imwrite(file_path, result)
                    
                    
                    module_menghitung_lapisan.lapisan(file_path,caminfo=2)
                    shutil.move(file_path,'folder_foto/')
                    state= False
            hapus_tempfile(folder_path)
            state = True
            time.sleep(3)
        elif res==[3,0,1]:
            print("tidak hitung")
            hapus_tempfile(folder_path)
            time.sleep(3)
    state = True   
    # Pembersihan 
    for oid in list(previous_centroids.keys()):
        if oid not in current_ids:
            previous_centroids.pop(oid, None)
            object_states.pop(oid, None)

    cv2.imshow('Karung Tracking', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()