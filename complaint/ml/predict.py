"""
UrbanSync — Machine Learning Inference Script
Demonstrates TWO SEPARATE Machine Learning Components:
1. Classification: TF-IDF + Logistic Regression -> BMC Municipal Category
2. Clustering: K-Means -> Civic Complaint Hotspot Detection

Usage:
  Interactive:
    python predict.py
  CLI arguments:
    python predict.py "There is a huge pothole on the road near my house" --lat 19.1197 --lon 72.8468
"""

import os
import sys
import pickle
import argparse

# Resolve model paths (checks root, ml/, and ml/model/)
def find_model_file(filename: str) -> str:
    possible_paths = [
        filename,
        os.path.join("ml", filename),
        os.path.join("ml", "model", filename),
        os.path.join("..", filename),
        os.path.join("..", "ml", "model", filename)
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return filename

# Load classification models using Python pickle
VEC_PATH = find_model_file("tfidf_vectorizer.pkl")
CLF_PATH = find_model_file("complaint_classifier.pkl")
KM_PATH = find_model_file("kmeans_model.pkl")
META_PATH = find_model_file("kmeans_cluster_info.pkl")

with open(VEC_PATH, "rb") as f:
    vectorizer = pickle.load(f)

with open(CLF_PATH, "rb") as f:
    classifier = pickle.load(f)

# Load clustering model using Python pickle
kmeans = None
cluster_metadata = None
if os.path.exists(KM_PATH):
    with open(KM_PATH, "rb") as f:
        kmeans = pickle.load(f)
if os.path.exists(META_PATH):
    with open(META_PATH, "rb") as f:
        cluster_metadata = pickle.load(f)

def predict_category(text: str) -> str:
    """Predicts BMC Municipal Category from complaint description"""
    cleaned = text.lower().strip()
    tfidf_vec = vectorizer.transform([cleaned])
    category = classifier.predict(tfidf_vec)[0]
    return category

def predict_hotspot(lat: float, lon: float):
    """Predicts geographical complaint hotspot cluster from coordinates"""
    if kmeans is None:
        return None, "K-Means model not loaded"
    cluster_id = int(kmeans.predict([[lat, lon]])[0])
    zone_name = f"Cluster {cluster_id}"
    if cluster_metadata and cluster_id < len(cluster_metadata):
        zone_name = cluster_metadata[cluster_id].get("zone_name", zone_name)
    return cluster_id, zone_name

def main():
    parser = argparse.ArgumentParser(description="UrbanSync Civic ML Inference")
    parser.add_argument("text", nargs="?", default=None, help="Complaint text description")
    parser.add_argument("--lat", type=float, default=None, help="Incident latitude")
    parser.add_argument("--lon", type=float, default=None, help="Incident longitude")
    args = parser.parse_args()

    complaint_text = args.text
    if not complaint_text:
        try:
            complaint_text = input("Enter your complaint description: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            return

    if not complaint_text:
        print("Error: Complaint description cannot be empty.")
        return

    # --- ML COMPONENT 1: CLASSIFICATION ---
    category = predict_category(complaint_text)
    print("\n" + "=" * 50)
    print("  ML COMPONENT 1: COMPLAINT CLASSIFICATION")
    print("=" * 50)
    print(f"Input:    \"{complaint_text}\"")
    print(f"Category: {category}")

    # --- ML COMPONENT 2: HOTSPOT CLUSTERING ---
    lat = args.lat
    lon = args.lon
    if lat is None and lon is None and sys.stdin.isatty():
        try:
            coord_input = input("\nEnter latitude & longitude (e.g. 19.1197, 72.8468) or press Enter to skip: ").strip()
            if coord_input and "," in coord_input:
                parts = coord_input.split(",")
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
        except (ValueError, EOFError):
            pass

    if lat is not None and lon is not None and kmeans is not None:
        cid, zone = predict_hotspot(lat, lon)
        print("\n" + "=" * 50)
        print("  ML COMPONENT 2: CIVIC HOTSPOT CLUSTERING")
        print("=" * 50)
        print(f"Coordinates:  ({lat:.4f}, {lon:.4f})")
        print(f"Cluster ID:   {cid}")
        print(f"Hotspot Zone: {zone}")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    main()