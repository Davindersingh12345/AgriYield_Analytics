from math import isfinite

REQUIRED = ["Crop", "Crop_Year", "Season", "State", "Area", "Production", "Annual_Rainfall", "Fertilizer", "Pesticide", "Yield"]
NUMERIC = ["Crop_Year", "Area", "Production", "Annual_Rainfall", "Fertilizer", "Pesticide", "Yield"]

def validate_record(payload):
    record = {}
    for field in ["Crop", "Season", "State"]:
        value = str(payload.get(field, "")).strip()
        if not value:
            return None, f"{field} is required."
        record[field] = value
    for field in NUMERIC:
        raw = payload.get(field, "")
        try:
            value = float(raw)
            if not isfinite(value):
                raise ValueError
            if field in ["Crop_Year", "Production"] and not value.is_integer():
                return None, f"{field} must be a whole number."
            if field != "Yield" and value < 0:
                return None, f"{field} cannot be negative."
            record[field] = int(value) if field in ["Crop_Year", "Production"] else value
        except (TypeError, ValueError):
            return None, f"{field} must be a valid number."
    return record, None
