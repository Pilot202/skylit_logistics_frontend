import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import shutil
import random
import string
import os
import json
import uuid
import numpy as np
import cv2
import tensorflow as tf
from tensorflow.keras.models import model_from_json
from passlib.context import CryptContext
from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from jose import JWTError, jwt
from datetime import datetime, timedelta

# --- CONFIGURATION ---
SECRET_KEY = "secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- APP INIT ---
app = FastAPI()
app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")

#--- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATABASE SETUP ---
Base = declarative_base()
engine = create_engine("sqlite:///./agriscan.db")
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    full_name = Column(String)
    otp_verified = Column(Integer, default=0)
    phone = Column(String)

class History(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True)
    user_email = Column(String)
    image_name = Column(String)
    prediction = Column(String)
    raw_scores = Column(Text)

Base.metadata.create_all(bind=engine)

# --- AUTHENTICATION ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user(email: str):
    db = SessionLocal()
    return db.query(User).filter(User.email == email).first()

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(email, password):
    user = get_user(email)
    if not user or not verify_password(password, user.password):
        return False
    return user

def create_access_token(data: dict, expires_delta=None):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = get_user(email)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

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

def generate_otp(length=6):
    otp = ''.join(random.choices(string.digits, k=length))
    print(f"🔐 OTP for user: {otp}")  # For development/debugging
    return otp

# --- ROUTES ---
otp_store = {}

@app.post("/signup")
def signup(email: str = Form(...), password: str = Form(...), full_name: str = Form(...), phone_number: str = Form(...)):
    db = SessionLocal()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = get_password_hash(password)
    user = User(email=email, password=hashed_pw, full_name=full_name, phone=phone_number)
    db.add(user)
    db.commit()
    otp_store[email] = generate_otp()
    return {"msg": "Signup successful. Please verify OTP."}

@app.post("/verify-otp")
def verify_otp(email: str = Form(...), otp: str = Form(...)):
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    expected_otp = otp_store.get(email)
    if not expected_otp or otp != expected_otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    user.otp_verified = 1
    db.commit()
    return {"msg": "OTP verified"}

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user or not user.otp_verified:
        raise HTTPException(status_code=401, detail="Invalid credentials or OTP not verified")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/profile")
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "full_name": current_user.full_name,
        "otp_verified": bool(current_user.otp_verified),
    }

@app.post("/predict")
async def predict(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    prediction, raw = predict_image(file_path)

    db = SessionLocal()
    db.add(History(user_email=current_user.email, image_name=file.filename, prediction=prediction, raw_scores=json.dumps(raw)))
    db.commit()

    return {
        "filename": file.filename,
        "prediction": prediction,
        "probabilities": {label_map[i]: float(p) for i, p in enumerate(raw)},
        "info": disease_info.get(prediction, {})
    }

@app.post("/predict-batch")
async def predict_batch(files: List[UploadFile] = File(...), current_user: User = Depends(get_current_user)):
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
        db.add(History(user_email=current_user.email, image_name=file.filename, prediction=prediction, raw_scores=json.dumps(raw)))
    db.commit()
    return results

@app.get("/history")
def get_history(current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    rows = db.query(History).filter(History.user_email == current_user.email).all()
    return [
        {"filename": row.image_name, "prediction": row.prediction, "scores": json.loads(row.raw_scores)}
        for row in rows
    ]

# Optional: Debug route for testing form submissions
@app.post("/debug-token")
async def debug_token(request: Request):
    form = await request.form()
    return {"received": dict(form)}

# --- RUN ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
