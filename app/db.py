import os
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.errors import PyMongoError

_client = None

def get_db():
    global _client
    if _client is None:
        uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        _client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    return _client[os.getenv("MONGO_DB", "agriyield_db")]

def ensure_indexes(db):
    crops = db.crops
    crops.create_index([("State", ASCENDING), ("Crop_Year", DESCENDING)], name="state_year_idx")
    crops.create_index([("Crop", ASCENDING), ("Season", ASCENDING)], name="crop_season_idx")
    crops.create_index([("Crop_Year", ASCENDING)], name="year_idx")
    crops.create_index([("Crop", TEXT), ("State", TEXT), ("Season", TEXT)], name="crop_text_idx")

def ping_database():
    try:
        get_db().command("ping")
        return True, "Connected to MongoDB"
    except PyMongoError as exc:
        return False, str(exc)
