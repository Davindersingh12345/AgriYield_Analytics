import os
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.errors import PyMongoError

_client = None

def get_db():
    global _client
    if _client is None:
        uri = os.getenv("MONGO_URI")

        if not uri:
            raise RuntimeError(
                "MONGO_URI environment variable is not configured"
            )

        _client = MongoClient(
            uri,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000
        )

    db_name = os.getenv("MONGO_DB", "agriyield_db")
    return _client[db_name]

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
