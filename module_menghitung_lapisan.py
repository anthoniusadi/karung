import cv2
import numpy as np
from ultralytics import YOLO
import database
import time
from count_karung import hitung,read

model_path = 'ncnn/alldataset.pt' 
#image_path = 'ujicoba/lapisan/var11.jpg'
db = '/home/epiphany/yolov11_project/db_cam1'

def lapisan(image_path,conf_threshold = 0.45,iou_threshold=0.45,toleransi=0.5):
    # 1. Load Model & Prediksi
    model = YOLO(model_path)
    results = model.predict(source=image_path, conf=conf_threshold, iou=iou_threshold, save=False)
    result = results[0]

    # 2. Ekstrak Data
    boxes = result.boxes.xyxy.cpu().numpy()

    if len(boxes) == 0:
        print("tidak ada objek terdeteksi")
        exit()

    objek = []
    tinggi = []

    for box in boxes:
        x1, y1, x2, y2 = box
        cy = (y1 + y2) / 2
        cx = (x1 + x2) / 2
        h = y2 - y1
        objek.append({'box': box, 'cx': cx, 'cy': cy, 'h': h})
        tinggi.append(h)

    # Hitung rata-rata tinggi karung untuk referensi toleransi
    avg_h = np.mean(tinggi)
    threshold = avg_h * toleransi

    # 3. ALGORITMA PENGELOMPOKAN BARIS (HORIZONTAL LAYER)
    # Urutkan dulu semua berdasarkan Y (posisi vertikal)
    objek.sort(key=lambda k: k['cy'])

    rows = []
    current_row = []
    simpan_lapisan=[]
    if objek:
        current_row.append(objek[0])

    for i in range(1, len(objek)):
        obj = objek[i]
        # Bandingkan Y objek ini dengan rata-rata Y baris saat ini
        avg_y_current_row = np.mean([o['cy'] for o in current_row])
        
        # Jika selisih Y < threshold, maka dia teman satu baris (horizontal)
        if abs(obj['cy'] - avg_y_current_row) < threshold:
            current_row.append(obj)
        else:
            # Jika jauh, tutup baris lama, mulai baris baru
            rows.append(current_row)
            current_row = [obj]

    # Masukkan baris terakhir
    if current_row:
        rows.append(current_row)

    # 4. VISUALISASI HASIL
    frame = cv2.imread(image_path)
    print(f"--- TERDETEKSI {len(rows)} LAPIS (BARIS) ---")

    total_obj = 0

    # Loop per Baris (Lapis Horizontal)
    for r_idx, row_objs in enumerate(rows):
        # Urutkan objek dalam baris dari kiri ke kanan (X)
        row_objs.sort(key=lambda k: k['cx'])
        
        count = len(row_objs)
        total_obj += count
        print(f"Lapis {r_idx+1}: {count} item")
        simpan_lapisan.append(count)
        # Gambar kotak dan label
        for c_idx, obj in enumerate(row_objs):
            x1, y1, x2, y2 = map(int, obj['box'])
            
            # Warna garis: Ganti warna tiap baris agar mudah dibedakan
            color = (0, 255, 0) if r_idx % 2 == 0 else (0, 165, 255) # Hijau / Oranye
            
            # Gambar Bounding Box Tipis
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1)
            
            # Label ID Grid (B=Baris, K=Kolom)
            label = f"B{r_idx+1}.K{c_idx+1}"
            
            # Background label agar tulisan terbaca
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
            cv2.rectangle(frame, (x1, y1 - 15), (x1 + w, y1), color, -1)
            cv2.putText(frame, label, (x1, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,0), 1)

        # Tulis total per baris di sisi kiri gambar
        avg_y_row = int(np.mean([o['cy'] for o in row_objs]))
        text_info = f"Lapis {r_idx+1}: {count}"
        cv2.putText(frame, text_info, (10, avg_y_row), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    print(simpan_lapisan[-1],simpan_lapisan[-2])
    #add database python
    #database.insert_data(simpan_lapisan[-1],simpan_lapisan[-2],111,len(simpan_lapisan),sum(simpan_lapisan))
    print("insert database done")
    # Tulis Total Keseluruhan di pojok kiri atas
    cv2.putText(frame, f"TOTAL: {total_obj}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    #read db camera depan data dari semua kamera harus sdh lengkap
    time.sleep(2)
    c1,c2=read(db)
    ## hitung jumlah karung
    print(c1,c2,total_obj)
    hasil = hitung(c1[0],c1[1],c2[0],c2[1],total_obj)
    print(hasil)
    # Tampilkan
    simpan_lapisan=[]

    # cv2.imshow("preview ", frame)
    # cv2.waitKey(0)
    cv2.destroyAllWindows()
