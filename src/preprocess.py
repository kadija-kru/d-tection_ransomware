import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
import joblib
import os

# --- Columns definitions ---
DROP_COLS = ["Family", "SeedAddress", "ExpAddress", "IPaddress"]
TARGET_COL = "Prediction"

NUM_COLS = ["Time", "BTC", "USD", "Netflow_Bytes", "Clusters", "Port",
            "bytes_per_second", "port_risk", "btc_flag", "usd_flag", "threat_score"]
CAT_COLS = ["Protocol", "Flag", "netflow_bucket"]

# --- Load dataset ---
def load_data(path: str):
    df = pd.read_csv(path)
    return df

# --- Clean and drop unused columns ---
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop(columns=DROP_COLS, errors="ignore")
    return df

# --- Convert label to binary for RL ---
def encode_target(df: pd.DataFrame):
    df['risk'] = df[TARGET_COL].apply(lambda x: 0 if x == 'A' else 1)
    return df

# --- Feature engineering ---
def feature_engineering(df: pd.DataFrame):
    # bytes per second
    df['bytes_per_second'] = df['Netflow_Bytes'] / (df['Time'] + 1)

    # netflow bucket
    try:
        df['netflow_bucket'] = pd.qcut(df['bytes_per_second'], q=3, labels=['low','medium','high'], duplicates='drop')
    except ValueError:
        df['netflow_bucket'] = pd.cut(df['bytes_per_second'], bins=3, labels=['low','medium','high'], duplicates='drop')

    # port risk
    risky_ports = [5061, 5062, 5063]
    df['port_risk'] = df['Port'].apply(lambda x: 1 if x in risky_ports else 0)

    # btc / usd flags
    df['btc_flag'] = (df['BTC'] > 0).astype(int)
    df['usd_flag'] = (df['USD'] > 0).astype(int)

    # threat score
    df['Threats'] = df['Threats'].fillna('Unknown')
    threat_mapping = {"Botnet":2, "Malware":2, "Normal":0, "Unknown":0}
    df['threat_score'] = df['Threats'].map(threat_mapping)

    return df

# --- Build preprocessing pipeline ---
def build_preprocess_pipeline():
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, NUM_COLS),
            ('cat', categorical_transformer, CAT_COLS)
        ]
    )

    pipeline = Pipeline(steps=[('preprocessor', preprocessor)])
    return pipeline

# --- Preprocess full dataset and save pipeline ---
def preprocess_data(df: pd.DataFrame, save_dir="models"):
    df = clean_data(df)
    df = encode_target(df)
    df = feature_engineering(df)

    y = df['risk']
    X = df.drop(columns=[TARGET_COL, 'risk'])

    pipeline = build_preprocess_pipeline()
    X_processed = pipeline.fit_transform(X, y)

    # save pipeline
    os.makedirs(save_dir, exist_ok=True)
    joblib.dump(pipeline, f"{save_dir}/feature_pipeline.pkl")

    return X_processed, y, pipeline

# --- Inference preprocessing for new/unseen data ---
def inference_preprocess(df: pd.DataFrame, pipeline_path="/content/d-tection_ransomware/models/feature_pipeline.pkl"):
    pipeline = joblib.load(pipeline_path)
    df = clean_data(df)
    df = feature_engineering(df)
    X_processed = pipeline.transform(df)
    return X_processed

# --- Example usage ---
if __name__ == "__main__":
    df = load_data("/content/d-tection_ransomware/data/UGRansome_Dataset_2024.csv")
    X, y, pipeline = preprocess_data(df)
    print("Processed features shape:", X.shape)
