"""
UrbanSync — Machine Learning Component 1: Complaint Classification Training
Model: TF-IDF Vectorizer + Multinomial Logistic Regression
Dataset: Mumbai BMC Civic Complaint Categorization Dataset v2
Target: bmc_category_15 (15 Municipal Service Categories)

Rules & Constraints:
- Uses ONLY Python `pickle` for model serialization (NO Joblib).
- Standard scikit-learn pipeline (TF-IDF + LogisticRegression).
- Evaluates Accuracy, Precision, Recall, F1-Score, and full Classification Report.
"""

import os
import re
import pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, precision_recall_fscore_support

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Candidate dataset paths
CANDIDATE_DATASET_PATHS = [
    os.path.join(BASE_DIR, "dataset", "mumbai_bmc_complaint_categorization_dataset_v2.csv"),
    os.path.join(BASE_DIR, "ml", "dataset", "mumbai_bmc_complaint_categorization_dataset_v2.csv"),
    os.path.join(BASE_DIR, "..", "dataset", "mumbai_bmc_complaint_categorization_dataset_v2.csv"),
]

def find_dataset():
    for p in CANDIDATE_DATASET_PATHS:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("Dataset CSV not found in candidate paths.")

def clean_complaint_text(text: str) -> str:
    """
    Standard reproducible text preprocessor:
    1. Handle nulls / non-strings
    2. Lowercase text
    3. Remove HTML tags & entities
    4. Remove URLs
    5. Remove non-alphanumeric punctuation
    6. Normalize whitespace
    """
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"<.*?>", " ", text)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def train_classification_model():
    dataset_path = find_dataset()
    print(f"[*] Loading complaint dataset from: {dataset_path}")
    df = pd.read_csv(dataset_path)
    total_raw = len(df)
    print(f"[*] Total raw records: {total_raw}")

    # Check for text column
    text_col = "complaint_text_clean_mumbai" if "complaint_text_clean_mumbai" in df.columns else "complaint_text_mumbai"
    target_col = "bmc_category_15"

    assert text_col in df.columns, f"Required text column '{text_col}' not found"
    assert target_col in df.columns, f"Target column '{target_col}' not found"

    # Preprocessing & deduplication
    print("[*] Cleaning text and removing duplicates...")
    df = df.dropna(subset=[text_col, target_col]).copy()
    df["clean_text"] = df[text_col].apply(clean_complaint_text)
    
    # Remove empty text records
    df = df[df["clean_text"].str.len() > 3]

    # Remove exact duplicate text complaints
    initial_len = len(df)
    df = df.drop_duplicates(subset=["clean_text", target_col])
    print(f"[*] Deduplicated from {initial_len} to {len(df)} records ({initial_len - len(df)} duplicates removed)")

    # 15 Category distribution
    print("\n[*] Category Distribution (15 BMC Categories):")
    cat_counts = df[target_col].value_counts()
    for cat, count in cat_counts.items():
        print(f"    - {cat:<30}: {count} records")

    X = df["clean_text"].values
    y = df[target_col].values

    # Train/Test Split (80/20 stratified)
    print("\n[*] Splitting dataset (80% Train, 20% Test, Stratified)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"    - Training set size: {len(X_train)}")
    print(f"    - Testing set size:  {len(X_test)}")

    # TF-IDF Vectorization
    print("\n[*] Vectorizing complaint text using TF-IDF...")
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=8000,
        sublinear_tf=True,
        min_df=2
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    print(f"    - Feature space dimensionality: {X_train_vec.shape[1]}")

    # Logistic Regression Classifier
    print("\n[*] Training Logistic Regression Classifier (TF-IDF + Logistic Regression)...")
    classifier = LogisticRegression(
        max_iter=1000,
        C=1.5,
        random_state=42,
        class_weight="balanced"
    )
    classifier.fit(X_train_vec, y_train)

    # Model Evaluation
    print("\n" + "=" * 60)
    print("       MODEL EVALUATION METRICS (TF-IDF + LOGISTIC REGRESSION)")
    print("=" * 60)
    y_pred = classifier.predict(X_test_vec)
    accuracy = accuracy_score(y_test, y_pred)
    prec_w, rec_w, f1_w, _ = precision_recall_fscore_support(y_test, y_pred, average="weighted")
    prec_m, rec_m, f1_m, _ = precision_recall_fscore_support(y_test, y_pred, average="macro")

    print(f"[*] Overall Accuracy:        {accuracy * 100:.2f}%")
    print(f"[*] Weighted Precision:      {prec_w * 100:.2f}%")
    print(f"[*] Weighted Recall:         {rec_w * 100:.2f}%")
    print(f"[*] Weighted F1-Score:       {f1_w * 100:.2f}%")
    print(f"[*] Macro F1-Score:          {f1_m * 100:.2f}%")

    print("\n[*] Full Classification Report:")
    print(classification_report(y_test, y_pred, digits=4))

    # Save models using Python pickle
    out_dirs = [
        BASE_DIR,
        os.path.join(BASE_DIR, "ml"),
        os.path.join(BASE_DIR, "ml", "model")
    ]
    for d in out_dirs:
        os.makedirs(d, exist_ok=True)
        vec_file = os.path.join(d, "tfidf_vectorizer.pkl")
        clf_file = os.path.join(d, "complaint_classifier.pkl")
        with open(vec_file, "wb") as f:
            pickle.dump(vectorizer, f, protocol=pickle.HIGHEST_PROTOCOL)
        with open(clf_file, "wb") as f:
            pickle.dump(classifier, f, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"[+] Saved models via pickle to: {d}")

    print("\n[SUCCESS] Classification Model Training & Evaluation Complete.")

if __name__ == "__main__":
    train_classification_model()
