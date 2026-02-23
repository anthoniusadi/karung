import cv2
import numpy as np
import time
from ultralytics import YOLO
from collections import defaultdict
import random
import shutil
from datetime import datetime
import os
import statistics
import module_menghitung_lapisan


count=random.randint(1,400)
# - Konfigurasi ---
WEIGHTS_PATH = 'ncnn/alldataset.pt' 
VIDEO_PATH = 'video_data/video_karung_6573.mp4'    
CONF_THRES = 0.45
IOU_THRES = 0.45
CLASS_NAMES = ['karung'] 

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

cap = cv2.VideoCapture(VIDEO_PATH)
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

# Output Video
#out = cv2.VideoWriter('ujicoba/output_video_'+str(count)+'.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 20, (frame_width, frame_height))

# Perhitungan Garis
column_x_r = int(frame_width * LINE_POSITION_RATIO_R)
column_x_l = int(frame_width * LINE_POSITION_RATIO_L)
CENTER_AREA_START_X = int(frame_width * CENTER_AREA_START_RATIO)
CENTER_AREA_END_X = int(frame_width * CENTER_AREA_END_RATIO)
temp=[]
pola={0,0,0}
def check(arah):
    if arah=={1,2,3}:
        print("tdk hitung")
        return False
    if arah=={3,2,1}:
        print("hitung")
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
    original = frame.copy()
    if not ret: break
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
            print(f"capture!{len(frame_centroids)}")
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
        print(f'TOTAL : {temp}')
        res = []
        num=0

        for item in temp:
            if item not in res:
                res.append(item)
        temp=[]
        print(f'result : {res}')
        if res==[3,0,1]:
            print("hitung")
            print(statistics.mode(modus))
            time.sleep(1)
            
            modus=[]
            num = 0
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if(file_path[-6:]=='_3.jpg') and state:
                    module_menghitung_lapisan.lapisan(file_path)
                    shutil.move(file_path,'folder_foto/')
                    state= False
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path) 
                        print(f"hapus file: {filename}")
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path) 
                        print(f"hapus directory: {filename}")
                except Exception as e:
                    print(f'Failed to delete {file_path}. {e}')
        elif res==[1,0,3]:
            print("tidak hitung")
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