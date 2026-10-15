import os, sys, json
from pathlib import Path
from datetime import datetime, timezone
from bson import ObjectId
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from pymongo import DESCENDING
from pymongo.errors import PyMongoError, DuplicateKeyError
from dotenv import load_dotenv
import pandas as pd
import joblib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")
from app.db import get_db, ensure_indexes, ping_database
from app.validation import validate_record

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("SECRET_KEY", "local-dev-key-change-me")
MODEL_PATH = ROOT / "ml" / "yield_model.joblib"

@app.template_filter("num")
def num(value):
    try: return f"{float(value):,.2f}"
    except (TypeError, ValueError): return value

def db_or_none():
    try:
        db = get_db()
        db.command("ping")
        return db
    except Exception:
        return None

def clean_doc(doc):
    if not doc: return doc
    doc["_id"] = str(doc["_id"])
    return doc

@app.route("/")
def dashboard():
    db = db_or_none()
    if db is None:
        return render_template("dashboard.html", connected=False, error="MongoDB is not reachable. Start the MongoDB service and refresh.", stats={}, states=[], crops=[], years=[], season_data=[], state_data=[], year_data=[])
    try:
        ensure_indexes(db)
        c = db.crops
        stats = {"records": c.count_documents({}), "states": len(c.distinct("State")), "crop_types": len(c.distinct("Crop")), "seasons": len(c.distinct("Season"))}
        states = sorted(c.distinct("State"))
        crops = sorted(c.distinct("Crop"))
        years = sorted(c.distinct("Crop_Year"), reverse=True)
        season_data = list(c.aggregate([{"$group":{"_id":"$Season","production":{"$sum":"$Production"}}},{"$sort":{"production":-1}},{"$limit":8}]))
        state_data = list(c.aggregate([{"$group":{"_id":"$State","production":{"$sum":"$Production"}}},{"$sort":{"production":-1}},{"$limit":10}]))
        year_data = list(c.aggregate([{"$group":{"_id":"$Crop_Year","production":{"$sum":"$Production"}}},{"$sort":{"_id":1}}]))
        recent = [clean_doc(d) for d in c.find({}, {"Crop":1,"Crop_Year":1,"Season":1,"State":1,"Area":1,"Production":1,"Yield":1}).sort("Crop_Year", DESCENDING).limit(8)]
        return render_template("dashboard.html", connected=True, error=None, stats=stats, states=states, crops=crops, years=years, season_data=season_data, state_data=state_data, year_data=year_data, recent=recent)
    except Exception as exc:
        return render_template("dashboard.html", connected=False, error=f"Database query failed: {exc}", stats={}, states=[], crops=[], years=[], season_data=[], state_data=[], year_data=[])

@app.route("/import", methods=["GET", "POST"])
def import_data():
    if request.method == "GET": return render_template("import.html")
    db = db_or_none()
    if db is None:
        flash("MongoDB is not reachable. Start MongoDB first.", "error"); return redirect(url_for("import_data"))
    csv_path = ROOT / "data" / "crop_yield.csv"
    if not csv_path.exists():
        flash("data/crop_yield.csv was not found.", "error"); return redirect(url_for("import_data"))
    try:
        df = pd.read_csv(csv_path)
        expected = ["Crop","Crop_Year","Season","State","Area","Production","Annual_Rainfall","Fertilizer","Pesticide","Yield"]
        missing = [col for col in expected if col not in df.columns]
        if missing: raise ValueError("Missing columns: " + ", ".join(missing))
        df = df[expected].dropna()
        docs = df.to_dict(orient="records")
        # Replace dataset for a reproducible first import; users should back up before re-importing.
        if request.form.get("mode") == "replace":
            db.crops.delete_many({})
        result = db.crops.insert_many(docs, ordered=False) if docs else None
        ensure_indexes(db)
        flash(f"Imported {len(result.inserted_ids) if result else 0:,} crop records into {db.name}.", "success")
    except Exception as exc:
        flash(f"Import failed: {exc}", "error")
    return redirect(url_for("dashboard"))

@app.route("/records")
def records():
    db = db_or_none()
    if db is None:
        flash("MongoDB is not reachable.", "error"); return render_template("records.html", records=[], query="", state="", crop="", page=1, pages=1)
    query = request.args.get("q", "").strip(); state = request.args.get("state", "").strip(); crop = request.args.get("crop", "").strip()
    page = max(1, request.args.get("page", 1, type=int)); per_page = 25
    filters = {}
    if state: filters["State"] = state
    if crop: filters["Crop"] = crop
    if query:
        filters["$or"] = [{"Crop":{"$regex":query,"$options":"i"}},{"State":{"$regex":query,"$options":"i"}},{"Season":{"$regex":query,"$options":"i"}}]
    total = db.crops.count_documents(filters); pages = max(1, (total + per_page - 1)//per_page)
    docs = [clean_doc(d) for d in db.crops.find(filters).sort([("Crop_Year", -1), ("State", 1)]).skip((page-1)*per_page).limit(per_page)]
    return render_template("records.html", records=docs, query=query, state=state, crop=crop, page=page, pages=pages)

@app.route("/records/add", methods=["GET", "POST"])
def add_record():
    if request.method == "POST":
        record, error = validate_record(request.form)
        if error: flash(error, "error"); return render_template("record_form.html", record=request.form, title="Add crop record")
        db = db_or_none()
        if db is None: flash("MongoDB is not reachable.", "error"); return redirect(url_for("add_record"))
        record["created_at"] = datetime.now(timezone.utc)
        db.crops.insert_one(record); flash("Crop record added.", "success"); return redirect(url_for("records"))
    return render_template("record_form.html", record={}, title="Add crop record")

@app.route("/records/<record_id>/edit", methods=["GET", "POST"])
def edit_record(record_id):
    db = db_or_none()
    if db is None: flash("MongoDB is not reachable.", "error"); return redirect(url_for("records"))
    try: oid = ObjectId(record_id)
    except Exception: flash("Invalid record ID.", "error"); return redirect(url_for("records"))
    old = db.crops.find_one({"_id":oid})
    if not old: flash("Record not found.", "error"); return redirect(url_for("records"))
    if request.method == "POST":
        record, error = validate_record(request.form)
        if error: flash(error, "error"); return render_template("record_form.html", record=request.form, title="Edit crop record")
        db.crops.update_one({"_id":oid},{"$set":record}); flash("Crop record updated.", "success"); return redirect(url_for("records"))
    return render_template("record_form.html", record=old, title="Edit crop record")

@app.route("/records/<record_id>/delete", methods=["POST"])
def delete_record(record_id):
    db = db_or_none()
    try:
        if db is None: raise RuntimeError("MongoDB is not reachable")
        result = db.crops.delete_one({"_id":ObjectId(record_id)})
        flash("Record deleted." if result.deleted_count else "Record not found.", "success" if result.deleted_count else "error")
    except Exception as exc: flash(f"Delete failed: {exc}", "error")
    return redirect(url_for("records"))

@app.route("/predict", methods=["GET", "POST"])
def predict():
    result = None
    options = {"Crop":[],"Season":[],"State":[]}
    db = db_or_none()
    if db is not None:
        for key in options: options[key] = sorted(db.crops.distinct(key))
    if request.method == "POST":
        if not MODEL_PATH.exists():
            flash("Prediction model not trained yet. Run: python ml/train_model.py", "error")
        else:
            try:
                bundle = joblib.load(MODEL_PATH)
                row = {"Crop":request.form["Crop"], "Crop_Year":int(request.form["Crop_Year"]), "Season":request.form["Season"], "State":request.form["State"], "Area":float(request.form["Area"]), "Annual_Rainfall":float(request.form["Annual_Rainfall"]), "Fertilizer":float(request.form["Fertilizer"]), "Pesticide":float(request.form["Pesticide"])}
                if any(row[k] < 0 for k in ["Area","Annual_Rainfall","Fertilizer","Pesticide"]): raise ValueError("Input quantities cannot be negative.")
                value = float(bundle["model"].predict(pd.DataFrame([row], columns=bundle["features"]))[0])
                result = {"yield":value, "inputs":row}
            except Exception as exc: flash(f"Could not make prediction: {exc}", "error")
    return render_template("predict.html", result=result, options=options)

@app.route("/query-lab")
def query_lab():
    db = db_or_none(); output=[]; error=None
    if db is None: error="MongoDB is not reachable."
    else:
        try:
            # Demonstration aggregation: top states by total production.
            output=list(db.crops.aggregate([{"$group":{"_id":"$State","records":{"$sum":1},"total_production":{"$sum":"$Production"},"avg_yield":{"$avg":"$Yield"}}},{"$sort":{"total_production":-1}},{"$limit":10}]))
        except Exception as exc: error=str(exc)
    return render_template("query_lab.html", output=output, error=error)

@app.route("/health")
def health():
    ok, message = ping_database()
    return jsonify({"status":"ok" if ok else "error", "mongodb":message}), (200 if ok else 503)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
