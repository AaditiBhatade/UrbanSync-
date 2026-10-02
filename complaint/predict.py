"""
UrbanSync — Machine Learning Prediction Script
Demonstrates TWO SEPARATE Machine Learning Components:
1. Classification: TF-IDF + Logistic Regression -> BMC Municipal Category
2. Clustering: K-Means -> Civic Complaint Hotspot Detection

Usage:
  python predict.py "There is a huge pothole on the road near my house."
  python predict.py "Garbage has not been collected for three days." --lat 19.0760 --lon 72.8777
  python predict.py (interactive prompt)
"""

import os
import sys
import pickle
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def find_file(filename: str) -> str:
    candidates = [
        os.path.join(BASE_DIR, filename),
        os.path.join(BASE_DIR, "ml", filename),
        os.path.join(BASE_DIR, "ml", "model", filename),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return os.path.join(BASE_DIR, filename)

# Load TF-IDF vectorizer and Logistic Regression classifier using pickle
vec_path = find_file("tfidf_vectorizer.pkl")
clf_path = find_file("complaint_classifier.pkl")

with open(vec_path, "rb") as f:
    vectorizer = pickle.load(f)

with open(clf_path, "rb") as f:
    classifier = pickle.load(f)

# Load K-Means clustering model using pickle
km_path = find_file("kmeans_model.pkl")
info_path = find_file("kmeans_cluster_info.pkl")

kmeans_model = None
cluster_info = None

if os.path.exists(km_path):
    with open(km_path, "rb") as f:
        kmeans_model = pickle.load(f)

if os.path.exists(info_path):
    with open(info_path, "rb") as f:
        cluster_info = pickle.load(f)

def predict_category(text: str) -> str:
    """
    ML Component 1: Predicts BMC category using TF-IDF + Logistic Regression.
    Notice: Does NOT return or display confidence to citizen.
    """
    cleaned = text.lower().strip()
    features = vectorizer.transform([cleaned])
    category = classifier.predict(features)[0]
    return category

def predict_hotspot(lat: float, lon: float):
    """
    ML Component 2: Predicts geographic complaint hotspot using K-Means.
    """
    if kmeans_model is None:
        return None, "Model not loaded"
    cluster_id = int(kmeans_model.predict([[lat, lon]])[0])
    zone_name = f"Cluster {cluster_id + 1}"
    if cluster_info:
        for c in cluster_info:
            if c.get("cluster_id") == cluster_id:
                zone_name = c.get("zone_name", zone_name)
                break
    return cluster_id, zone_name

def main():
    parser = argparse.ArgumentParser(description="UrbanSync Civic Complaint Prediction")
    parser.add_argument("text", nargs="?", default=None, help="Complaint text description")
    parser.add_argument("--lat", type=float, default=None, help="Latitude")
    parser.add_argument("--lon", type=float, default=None, help="Longitude")
    args = parser.parse_args()

    complaint_text = args.text
    if not complaint_text:
        try:
            complaint_text = input("Enter your complaint description: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExited.")
            return

    if not complaint_text:
        print("Error: Complaint text is required.")
        return

    # ML COMPONENT 1: CLASSIFICATION
    category = predict_category(complaint_text)

    print("\n" + "=" * 55)
    print("  ML COMPONENT 1: COMPLAINT CLASSIFICATION")
    print("=" * 55)
    print(f"Input:              \"{complaint_text}\"")
    print(f"Predicted Category: {category}")

    # ML COMPONENT 2: CLUSTERING (if coordinates provided)
    if args.lat is not None and args.lon is not None:
        cluster_id, zone_name = predict_hotspot(args.lat, args.lon)
        print("\n" + "=" * 55)
        print("  ML COMPONENT 2: CIVIC COMPLAINT HOTSPOT DETECTION")
        print("=" * 55)
        print(f"Coordinates:        ({args.lat:.4f}, {args.lon:.4f})")
        print(f"Hotspot Cluster:    Cluster {cluster_id} -> {zone_name}")
    print("=" * 55 + "\n")

if __name__ == "__main__":
    main()
