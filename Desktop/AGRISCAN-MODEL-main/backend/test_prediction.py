import tensorflow as tf
import numpy as np
from PIL import Image
import json
from tensorflow.keras.models import model_from_json
import pathlib
import cv2

import os

# === 1. Load model architecture ===
# Load the model architecture from the JSON file
# Using the path from previous successful loads
json_file = open("C:/Users/USER/Desktop/AGRISCAN-MODEL-main/backend/model/agroscanmodel1_architecture.json", 'r')
loaded_model_json = json_file.read()
json_file.close()
model = model_from_json(loaded_model_json)

# Load the weights into the new model
# Using the path from previous successful loads
model.load_weights('C:/Users/USER/Desktop/AGRISCAN-MODEL-main/backend/model/agroscanmodel1_weights.weights.h5')

# Compile the model after loading the weights (important for evaluation and prediction)
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

print("Model loaded successfully!")



# Define the path to your JSON file containing disease information
disease_info_path = './maize_plant_diseases_info.json' # Assuming the file is in your Google Drive

# Load the disease information from the JSON file
try:
    with open(disease_info_path, 'r') as f:
        disease_info = json.load(f)
except FileNotFoundError:
    print(f"Error: Disease information file not found at {disease_info_path}")
    disease_info = {} # Initialize as empty dictionary if file not found
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from {disease_info_path}")
    disease_info = {} # Initialize as empty dictionary if JSON is invalid



# Define the dictionary to map numerical labels to disease names
maize_disease_labels_num= {
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
    11: 'maize_smuts',
}


# === 3. Preprocess image ===
# Load and preprocess the images from the list of paths
def load_and_preprocess_image(image_path, img_height, img_width):
  """
  Loads and preprocesses a single image for model prediction.

  Args:
    image_path: Path to the image file.
    img_height: The target height for resizing.
    img_width: The target width for resizing.

  Returns:
    A NumPy array containing the preprocessed image, ready for prediction.
    Returns None if the image cannot be loaded or processed.
  """
  if not os.path.exists(image_path):
    print(f"Error: Image file not found at {image_path}")
    return None

  img = cv2.imread(image_path)

  if img is None:
    print(f"Error: Could not load image from {image_path}")
    return None

  resized_img = cv2.resize(img, (img_width, img_height))

  # Add a batch dimension to the image
  processed_img = np.expand_dims(resized_img, axis=0)

  return processed_img

# Example usage: Replace 'path/to/your/image.jpg' with the actual image path
# You also need to know the expected input shape of your model (e.g., 244x244)
image_to_predict_path = "C:/Users/USER/Desktop/AGRISCAN-MODEL-main/backend/test_images/Corn_Health.jpg" # Replace with a valid image path
img_height = 244
img_width = 244

processed_image = load_and_preprocess_image(image_to_predict_path, img_height, img_width)

if processed_image is not None:
    # === 4. Make prediction ===
    predictions = model.predict(processed_image)
    print("Raw predictions:", predictions)

    # Get the predicted class index
    predicted_class_index = np.argmax(predictions)

    # Get the predicted disease label
    predicted_disease = maize_disease_labels_num[predicted_class_index]

    print("Predicted class index:", predicted_class_index)
    print("Predicted disease:", predicted_disease)

    # === 5. Display disease information from JSON ===
    if predicted_disease in disease_info:
        info = disease_info[predicted_disease]
        print(f"\nInformation for {predicted_disease.replace('_', ' ').title()}:") # Format the disease name
        print("Symptoms:", info.get('symptoms', 'N/A'))
        print("Prevention:", info.get('prevention', 'N/A'))
        print("Control:", info.get('control', 'N/A'))
        print("Chemicals:", ", ".join(info.get('chemicals', ['N/A']))) # Join chemicals with commas
    else:
        print(f"\nNo detailed information found for: {predicted_disease}")

else:
    print("Image processing failed. Cannot make prediction.")


from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import uvicorn
import os
import numpy as np
import json
import shutil
import cv2
import uuid
import tensorflow as tf
from tensorflow.keras.models import model_from_json
from datetime import datetime, timedelta
import jwt

# === CONFIG ===
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
UPLOAD_DIR = "uploaded_images"
HISTORY_FILE = "history.json"
MODEL_ARCH_PATH = "model/agroscanmodel1_architecture.json"
MODEL_WEIGHTS_PATH = "model/agroscanmodel1_weights.weights.h5"
DISEASE_INFO_PATH = "maize_plant_diseases_info.json"

os.makedirs(UPLOAD_DIR, exist_ok=True)

# === LOAD MODEL ===
with open(MODEL_ARCH_PATH, "r") as f:
    model = model_from_json(f.read())
model.load_weights(MODEL_WEIGHTS_PATH)
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# === LOAD DISEASE INFO ===
with open(DISEASE_INFO_PATH, 'r') as f:
    disease_info = json.load(f)

# === DISEASE LABELS ===
maize_disease_labels_num = {
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
    11: 'maize_smuts',
}

# === FASTAPI SETUP ===
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

fake_users_db = {
    "testuser": {
        "username": "testuser",
        "password": "testpass"
    }
}

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str

class PredictionResult(BaseModel):
    filename: str
    predicted_disease: str
    confidence: float
    info: dict

# === AUTH ===
def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if user and user["password"] == password:
        return user
    return None

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# === IMAGE PROCESSING ===
def preprocess_image(img_path):
    img = cv2.imread(img_path)
    resized_img = cv2.resize(img, (244, 244))
    return np.expand_dims(resized_img, axis=0)

def predict_image(img_path):
    img = preprocess_image(img_path)
    predictions = model.predict(img)[0]
    pred_index = np.argmax(predictions)
    label = maize_disease_labels_num[pred_index]
    confidence = float(predictions[pred_index])
    info = disease_info.get(label, {})
    return label, confidence, info

def save_history(username, prediction_data):
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    history.append({"username": username, **prediction_data})
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

# === ROUTES ===
@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token({"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/predict", response_model=List[PredictionResult])
def predict_batch(
    files: List[UploadFile] = File(...),
    current_user: str = Depends(get_current_user)
):
    results = []
    for file in files:
        temp_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.jpg")
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        predicted_disease, confidence, info = predict_image(temp_path)
        prediction_data = {
            "filename": file.filename,
            "predicted_disease": predicted_disease,
            "confidence": confidence,
            "info": info
        }
        save_history(current_user, prediction_data)
        results.append(prediction_data)
        os.remove(temp_path)
    return results

@app.get("/history")
def get_user_history(current_user: str = Depends(get_current_user)):
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        all_history = json.load(f)
    return [entry for entry in all_history if entry["username"] == current_user]

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
