"""Train a baseline yield regression model from the supplied CSV."""
from pathlib import Path
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.base import clone

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "crop_yield.csv"
MODEL = ROOT / "ml" / "yield_model.joblib"
METRICS = ROOT / "ml" / "model_metrics.txt"

def main():
    df = pd.read_csv(CSV)
    # Remove impossible/missing rows and extreme invalid target values only if absent/non-finite.
    df = df.dropna(subset=["Crop", "Season", "State", "Yield"])
    df = df[df["Yield"].apply(lambda x: pd.notna(x) and abs(float(x)) < 1e12)]
    features = ["Crop", "Crop_Year", "Season", "State", "Area", "Annual_Rainfall", "Fertilizer", "Pesticide"]
    target = "Yield"
    X, y = df[features], df[target].astype(float)
    categorical = ["Crop", "Season", "State"]
    numeric = [c for c in features if c not in categorical]
    preprocessor = ColumnTransformer([
        ("categorical", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical),
        ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric),
    ])
    model = Pipeline([("preprocess", preprocessor), ("regressor", RandomForestRegressor(n_estimators=160, min_samples_leaf=2, random_state=42, n_jobs=-1))])
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    metrics = f"Rows used: {len(df)}\nFeatures: {', '.join(features)}\nMAE: {mean_absolute_error(y_test, pred):.6f}\nRMSE: {mean_squared_error(y_test, pred) ** 0.5:.6f}\nR2: {r2_score(y_test, pred):.6f}\n\nNote: Yield values have a wide range in the supplied data. Metrics are a baseline and should be interpreted alongside crop-specific validation."
    MODEL.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": features}, MODEL)
    METRICS.write_text(metrics, encoding="utf-8")
    print(metrics)
    print(f"Saved model: {MODEL}")

if __name__ == "__main__":
    main()
