
import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib

DROP_COLS = ["Family", "SeedAddress", "ExpAddress", "IPaddress"]

TARGET_COL = "Prediction"

NUM_COLS = ["Time", "BTC", "USD", "Netflow_Bytes", "Clusters", "Port"]
CAT_COLS = ["Protocol", "Flag", "Threats"]


def load_data(path: str):
    df = pd.read_csv(path)
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Drop leakage + unused columns."""
    df = df.drop(columns=DROP_COLS, errors="ignore")
    return df


def encode_target(df: pd.DataFrame):
    """Map Prediction → integer labels"""
    mapping = {"A": 0, "S": 1, "SS": 2}
    df[TARGET_COL] = df[TARGET_COL].map(mapping)
    return df, mapping


def build_preprocess_pipeline():
    """Creates reusable scikit ColumnTransformer pipeline."""

    # numeric → scale
    num_processor = Pipeline(steps=[
        ("scaler", StandardScaler())
    ])

    # categorical → onehot
    cat_processor = Pipeline(steps=[
        ("encoder", OneHotEncoder(handle_unknown="ignore"))
    ])

    preproc = ColumnTransformer(
        transformers=[
            ("num", num_processor, NUM_COLS),
            ("cat", cat_processor, CAT_COLS),
        ]
    )

    return preproc


def preprocess_data(df: pd.DataFrame, save_dir="artifacts"):
    """Preprocess fully & save transformers"""

    df = clean_data(df)
    df, mapping = encode_target(df)

    y = df[TARGET_COL]
    X = df.drop(columns=[TARGET_COL])

    preproc = build_preprocess_pipeline()
    X_processed = preproc.fit_transform(X)

    # Save artifacts
    joblib.dump(preproc, f"{save_dir}/preprocessor.pkl")
    joblib.dump(mapping, f"{save_dir}/label_mapping.pkl")

    return X_processed, y


def inference_preprocess(df: pd.DataFrame, preproc_path="artifacts/preprocessor.pkl"):
    """Used for new/unseen data."""
    preproc = joblib.load(preproc_path)
    X = preproc.transform(df)
    return X
