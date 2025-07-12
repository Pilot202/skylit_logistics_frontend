from tensorflow.keras.models import model_from_json
import json

def load_model():
    with open("model/agroscanmodel1_architecture.json", "r") as f:
        model_json = f.read()
    model = model_from_json(model_json)
    model.load_weights("model/agroscanmodel1_weights.weights.h5")
    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
    return model

def load_disease_info():
    with open("model/maize_plant_diseases_info.json", "r") as f:
        return json.load(f)
