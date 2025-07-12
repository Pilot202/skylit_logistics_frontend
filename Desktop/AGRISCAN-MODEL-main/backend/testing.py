import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import shutil
import os
import json
import uuid
import numpy as np
import cv2
import tensorflow as tf
from tensorflow.keras.models import model_from_json
from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# --- CONFIGURATION ---
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- APP INIT ---
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "AgriScan backend running"}

# --- DATABASE SETUP ---
Base = declarative_base()
engine = create_engine("sqlite:///./agriscan.db")
SessionLocal = sessionmaker(bind=engine)

class History(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True)
    user_email = Column(String, default="anonymous")  # Dummy user
    image_name = Column(String)
    prediction = Column(String)
    raw_scores = Column(Text)

Base.metadata.create_all(bind=engine)

# --- MODEL LOADING ---
with open("model/agroscanmodel1_architecture.json") as f:
    model = model_from_json(f.read())

model.load_weights("model/agroscanmodel1_weights.weights.h5")
model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])

with open("maize_plant_diseases_info.json") as f:
    disease_info = json.load(f)

label_map = {
    0: "maize_ear_rot",
    1: "maize_grasshopper",
    2: "Maize_fall_armyworm",
    3: "maize_leaf_beetle",
    4: "maize_healthy",
    5: "maize_lethal_necrosis",
    6: "maize_leaf_blight",
    7: "maize_leaf_spot",
    8: "Maize_streak_virus",
    9: "maize_nutrient_deficiency",
    10: "maize_rust",
    11: "maize_smuts",
}

# --- HELPERS ---
def preprocess_image(file_path):
    img = cv2.imread(file_path)
    img = cv2.resize(img, (244, 244))
    return np.expand_dims(img, axis=0)

def predict_image(image_path):
    img = preprocess_image(image_path)
    preds = model.predict(img)
    pred_index = int(np.argmax(preds))
    pred_label = label_map[pred_index]
    return pred_label, preds.tolist()[0]

# --- ROUTES ---

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    prediction, raw = predict_image(file_path)

    db = SessionLocal()
    db.add(History(user_email="anonymous", image_name=file.filename, prediction=prediction, raw_scores=json.dumps(raw)))
    db.commit()

    return {
        "filename": file.filename,
        "prediction": prediction,
        "probabilities": {label_map[i]: float(p) for i, p in enumerate(raw)},
        "info": disease_info.get(prediction, {})
    }

@app.post("/predict-batch")
async def predict_batch(files: List[UploadFile] = File(...)):
    results = []
    db = SessionLocal()
    for file in files:
        path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        prediction, raw = predict_image(path)
        results.append({
            "filename": file.filename,
            "prediction": prediction,
            "probabilities": {label_map[i]: float(p) for i, p in enumerate(raw)},
            "info": disease_info.get(prediction, {})
        })
        db.add(History(user_email="anonymous", image_name=file.filename, prediction=prediction, raw_scores=json.dumps(raw)))
    db.commit()
    return results

@app.get("/history")
def get_history():
    db = SessionLocal()
    rows = db.query(History).all()
    return [
        {"filename": row.image_name, "prediction": row.prediction, "scores": json.loads(row.raw_scores)}
        for row in rows
    ]
# Mount static only after defining API endpoints
app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")

# --- RUN ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)



