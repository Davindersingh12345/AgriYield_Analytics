# AgriYield Analytics

A MongoDB + Flask mini project using the supplied crop-yield dataset. Includes dashboard charts, CSV import, CRUD, indexes, aggregation reports, a scikit-learn yield prediction baseline, and an optional Node.js/Mongoose API.

## 1. Requirements
- Windows 10/11 (or Linux/macOS)
- Python 3.10+ (3.11 recommended)
- MongoDB Community Server running locally on port 27017
- Optional: MongoDB Compass; Node.js 18+ for the optional Mongoose example

## 2. Install MongoDB
Install MongoDB Community Server for your operating system. On Windows, install it as a service if the installer offers that option. Open MongoDB Compass and connect to `mongodb://localhost:27017/`. The app creates the `agriyield_db` database and `crops` collection when data is imported.

Check service status in PowerShell:
```powershell
Get-Service MongoDB
Start-Service MongoDB
```
If the service has a different name or you chose not to install it as a service, start `mongod` using your configured data directory instead.

## 3. Setup the Flask application (Windows PowerShell)
Open PowerShell in the `agriyield_mongodb` project folder:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```
If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that same terminal, then activate again. Edit `.env` only if your MongoDB URI differs.

## 4. Import data and run
```powershell
python -m app.main
```
Open `http://127.0.0.1:5000`. Select **Import dataset** and choose **Append records** on a clean database. The bundled CSV has 19,689 records. If you import repeatedly in append mode, duplicates will be created; use Replace only when you intend to clear existing crop records first. Back up before replacing data.

Health check: `http://127.0.0.1:5000/health` should return a JSON status of `ok` when MongoDB is available.

## 5. Train the prediction model
In a second terminal (with the same virtual environment activated):
```powershell
python ml/train_model.py
```
The script creates `ml/yield_model.joblib` and `ml/model_metrics.txt`. Then refresh the app and open **Yield prediction**. Training may take a few minutes depending on your computer. The model artifact is not bundled; generate it locally from your CSV.

The target `Yield` has a wide range across crops. Treat the prediction as a classroom demonstration, not a guaranteed forecast or agronomic recommendation.

## 6. Explore MongoDB in Compass
1. Connect to `mongodb://localhost:27017/`.
2. Open `agriyield_db` → `crops`.
3. Inspect BSON documents and field types.
4. Open the Indexes tab to see indexes created by the app.
5. Use the Aggregations tab to test the pipeline in `docs/SUBMISSION_REPORT.md`.

## 7. Useful mongosh commands
```javascript
use agriyield_db
db.crops.countDocuments()
db.crops.findOne()
db.crops.getIndexes()
db.crops.find({State: "Punjab"}).explain("executionStats")
db.crops.find({Crop: "Wheat", Season: "Rabi"}).explain("executionStats")
```
Field values vary in the CSV; adjust the example filters to actual values in your imported data. To demonstrate a compound-index query, try:
```javascript
db.crops.find({State: "Punjab", Crop_Year: {$gte: 2010}}).sort({Crop_Year: -1}).explain("executionStats")
```
Compare `executionStats.executionStages` and `totalDocsExamined` before/after an appropriate index. Do not drop production data to experiment.

## 8. Optional Node.js + Mongoose integration
```powershell
cd node_integration
Copy-Item .env.example .env
npm install
npm start
```
API endpoints: `GET /health`, `GET /api/crops`, `POST /api/crops`, `PATCH /api/crops/:id`, `DELETE /api/crops/:id`. Example POST body:
```json
{"Crop":"Demo Crop","Crop_Year":2025,"Season":"Rabi","State":"Punjab","Area":10,"Production":20,"Annual_Rainfall":500,"Fertilizer":100,"Pesticide":2,"Yield":2}
```
Use Postman or curl. This optional API uses the same `crops` collection; the Flask app remains the primary interface.

## 9. Project structure
```text
agriyield_mongodb/
├── app/
│   ├── main.py              # Flask routes and dashboard
│   ├── db.py                # MongoDB connection and indexes
│   ├── validation.py        # Application input validation
│   ├── templates/           # Jinja HTML pages
│   └── static/style.css     # Responsive UI
├── data/crop_yield.csv      # Supplied dataset
├── ml/train_model.py        # Model training and evaluation
├── node_integration/        # Optional Node.js/Mongoose API
├── docs/SUBMISSION_REPORT.md
├── requirements.txt
└── README.md
```

## 10. Troubleshooting
- **ServerSelectionTimeoutError / MongoDB unreachable:** make sure the MongoDB service is running and `MONGO_URI` is correct.
- **No records on dashboard:** import the CSV from the Import dataset page.
- **No prediction model:** run `python ml/train_model.py` after installing requirements.
- **Port 5000 busy:** change the port in the last line of `app/main.py`.
- **Charts do not load:** Chart.js is loaded from a CDN, so check internet connectivity. Tables and database routes do not depend on the charts.

## 11. Syllabus coverage
See `docs/SUBMISSION_REPORT.md` for unit-wise mapping, database design, indexes, aggregation, testing, limitations and viva preparation notes.
