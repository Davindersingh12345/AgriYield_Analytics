# AgriYield Analytics — MongoDB Crop Yield Analysis and Prediction System

## Abstract
AgriYield Analytics is a mini-project that stores and explores agricultural crop records using MongoDB. A Flask web application provides a dashboard, CRUD operations, dataset import, aggregation reports and a machine-learning yield estimate. PyMongo connects the Python application to MongoDB Community Edition. An optional Node.js/Mongoose API demonstrates the second integration pathway in the syllabus.

## Problem statement
Agricultural datasets contain useful patterns across crops, seasons, states, years, rainfall, area, fertilizer and pesticide usage. The project organizes these records in a document database and provides practical queries and visual summaries so users can explore the dataset. Its ML component provides an educational baseline prediction, not professional agronomic advice.

## Objectives
1. Explain NoSQL and document-oriented storage with MongoDB.
2. Import and manage crop data using CRUD operations.
3. Demonstrate document schema validation and relationships/design choices.
4. Add single-field, compound and text indexes.
5. Use aggregation pipelines for summaries and comparisons.
6. Connect MongoDB with Flask/PyMongo and demonstrate Node.js/Mongoose.
7. Train and evaluate a baseline regression model using historical crop data.

## Dataset
File: `data/crop_yield.csv`. Initial inspection: 19,689 rows, 10 columns, no missing values in the supplied file. Fields: Crop, Crop_Year, Season, State, Area, Production, Annual_Rainfall, Fertilizer, Pesticide and Yield. The project does not assume units for all numeric fields beyond those documented by the dataset provider; check the original source before making real-world comparisons.

## Architecture
Browser → Flask routes/templates → PyMongo → MongoDB database `agriyield_db`, collection `crops`. The ML training script reads the CSV, trains a scikit-learn preprocessing/model pipeline and saves `ml/yield_model.joblib`; Flask loads the model for prediction. The optional Node API uses Mongoose and the same `crops` collection.

## Database design
Each crop observation is stored as a MongoDB document with the ten dataset fields. Additional app-created records may include `created_at`. The supplied dataset is naturally represented as flat observation documents because each row describes one crop/state/season/year observation. This project does not create artificial relationships where the dataset has no stable crop or state IDs. A production design could normalize reference entities into `states` and `crop_catalog` collections and reference them by ObjectId if metadata needed independent management.

### Validation
Application-level validation requires all ten fields; Crop, Season and State must be non-empty; numeric values must be finite; negative values are rejected except the Yield target is allowed to be zero or positive. The Node/Mongoose example adds schema-level validation. For production, also add MongoDB collection JSON Schema validation through `collMod` and audit source-specific units and valid ranges.

### Indexes
- `{ State: 1, Crop_Year: -1 }`: supports state/year filtering and ordering.
- `{ Crop: 1, Season: 1 }`: supports crop/season filters.
- `{ Crop_Year: 1 }`: supports year filtering.
- text index on Crop, State and Season: supports `$text` search where used.

Indexes speed supported queries but consume storage and make writes more expensive. Validate their value with `explain("executionStats")` on representative queries.

## Aggregation example
The Aggregation Lab groups documents by State, counts records, sums Production, averages Yield, sorts by production descending and returns the top ten. The dashboard additionally groups production by Season and Crop_Year.

## Machine learning
A RandomForestRegressor pipeline one-hot encodes Crop/Season/State and scales numeric inputs. A reproducible 80/20 split is used. MAE, RMSE and R² are written to `ml/model_metrics.txt`. Yield values may have a very wide range across crop types, so aggregate metrics can be misleading. For better evaluation, report crop-specific errors, check for leakage and units, compare against a simple baseline, and consider log-target or crop-specific models. Production use requires domain review and external validation.

## Unit-wise syllabus mapping
| Syllabus unit | Project implementation |
|---|---|
| I. Introduction to NoSQL and MongoDB | Document database; local Community Edition setup; Compass; Atlas is covered in viva/documentation; discuss CAP trade-offs. |
| II. MongoDB basics and CRUD | CSV import, `crops` collection, records list, add/edit/delete, PyMongo queries and indexes. |
| III. Schema design and data modeling | Flat observation-document model, validation in `app/validation.py`, discussion of embedding vs referencing and relationships. |
| IV. Indexing and aggregation | Index creation in `app/db.py`; Aggregation Lab; dashboard aggregation; explain() exercise in README. |
| V. MongoDB integration | Flask + PyMongo application and optional Node.js + Mongoose CRUD API. |
| VI. Project and AI trends | Dashboard, prediction pipeline, model metrics, production best practices and future-work section. |

## Testing checklist
1. Start MongoDB and confirm `/health` returns HTTP 200.
2. Import the dataset and verify collection count is 19,689 on the first clean import.
3. Search records by crop/state/season and test pagination.
4. Add a valid record, edit it and delete it.
5. Submit invalid values (blank name, negative area, invalid year) and verify rejection.
6. Open dashboard and Aggregation Lab; compare top-state aggregation with Compass.
7. Train model and submit prediction form; verify prediction is numeric.
8. Use `explain("executionStats")` to compare query plans before/after an index.
9. Optional: start the Mongoose server and test `/api/crops` endpoints.

## Limitations and future work
- Yield definition, units and data provenance should be confirmed from the original source.
- Historical patterns do not guarantee future outcomes.
- Add user authentication, audit logs, backups, rate limits, automated tests, Docker deployment, collection-level JSON Schema validation and role-based access before production.
- Future versions could add weather APIs, district-level forecasts, crop-specific models, explainability, anomaly detection and AI-assisted natural-language query suggestions with human review.

## Conclusion
The project demonstrates the core MongoDB course outcomes in a single runnable application: document storage, CRUD, indexing, aggregation, Python and Node integrations, plus an applied predictive analytics component.
