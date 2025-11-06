import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
import joblib
import os

def load_data(path):
    return pd.read_csv(path)

def create_target(df):
    mapping = {"S": 0, "SS": 1, "A": 1}
    df["risk"] = df["Prediction"].map(mapping)
    return df

def preprocess(df):

    # Drop IPaddress — too many unique addresses
    df = df.drop(columns=["IPaddress"])

    # Time bucketing
    # Option: leave numeric or bucket into ranges
    df["Time"] = df["Time"].astype(int)

    # Define feature groups
    categorical = ["Protocol", "Flag", "Family", "Threats"]
    numeric = ["Time", "Clusters", "BTC", "USD", "Netflow_Bytes", "Port"]

    ct = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
            ("num", StandardScaler(), numeric)
        ]
    )

    X = df[categorical + numeric]
    y = df["risk"]

    pipeline = Pipeline([
        ("preprocess", ct)
    ])

    X_processed = pipeline.fit_transform(X)

    return X_processed, y, pipeline


def train_test_store(df, pipeline):

    X_processed, y, _ = preprocess(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X_processed, y, test_size=0.2, random_state=42, stratify=y
    )

    os.makedirs("data/processed", exist_ok=True)

    # Save arrays
    np.save("data/processed/X_train.npy", X_train)
    np.save("data/processed/X_test.npy", X_test)
    np.save("data/processed/y_train.npy", y_train)
    np.save("data/processed/y_test.npy", y_test)

    # Save preprocessing pipeline
    os.makedirs("models", exist_ok=True) # Ensure models directory exists
    joblib.dump(pipeline, "models/preprocess.pkl")

    print("✅ Saved processed data + preprocess artifacts.")


if __name__ == "__main__":
    df = load_data("data/UGRansome_Dataset_2024.csv")
    df = create_target(df)
    X_processed, y, pipeline = preprocess(df)
    train_test_store(df, pipeline)
