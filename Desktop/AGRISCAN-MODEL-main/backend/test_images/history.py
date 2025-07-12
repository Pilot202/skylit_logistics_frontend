history_db = {}

def save_prediction(username: str, filename: str, predicted_class: str):
    if username not in history_db:
        history_db[username] = []
    history_db[username].append({"filename": filename, "prediction": predicted_class})

def get_user_history(username: str):
    return history_db.get(username, [])
