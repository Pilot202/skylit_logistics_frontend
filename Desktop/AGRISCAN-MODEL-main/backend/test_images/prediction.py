from fastapi import APIRouter, UploadFile, File, Depends
from typing import List
from .model_loader import load_model, load_disease_info
from .utils import preprocess_image, save_upload, disease_map
from .history import save_prediction
from .auth import get_current_user
import numpy as np

router = APIRouter()

model = load_model()
disease_info = load_disease_info()

@router.post("/predict")
async def predict(images: List[UploadFile] = File(...), current_user=Depends(get_current_user)):
    results = []
    for image in images:
        path = save_upload(image)
        img = preprocess_image(path)
        preds = model.predict(img)
        class_id = int(np.argmax(preds))
        label = disease_map[class_id]
        save_prediction(current_user.username, image.filename, label)
        results.append({
            "filename": image.filename,
            "predicted_class": label,
            "probabilities": preds.tolist()[0],
            "details": disease_info.get(label, {})
        })
    return results
