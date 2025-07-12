import cv2
import numpy as np
import os
import shutil
from uuid import uuid4

disease_map = {
    0: 'maize_ear_rot',
    1: 'maize_grasshopper',
    2: 'Maize_fall_armyworm',
    3: 'maize_leaf_beetle',
    4: 'maize_healthy',
    5: 'maize_lethal_necrosis',
    6: 'maize_leaf_blight',
    7: 'maize_leaf_spot',
    8: 'Maize_streak_virus',
    9: 'maize_nutrient_deficiency',
    10: 'maize_rust',
    11: 'maize_smuts'
}

def preprocess_image(image_path, size=(244, 244)):
    img = cv2.imread(image_path)
    img = cv2.resize(img, size)
    return np.expand_dims(img, axis=0)

def save_upload(file, upload_dir="uploads"):
    os.makedirs(upload_dir, exist_ok=True)
    path = os.path.join(upload_dir, f"{uuid4().hex}_{file.filename}")
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return path
