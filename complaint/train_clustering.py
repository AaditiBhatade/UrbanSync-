"""
UrbanSync — Machine Learning Component 2: Civic Complaint Hotspot Detection
Model: K-Means Clustering (Unsupervised Machine Learning)
Features: Latitude, Longitude (Mumbai Civic Complaint Dataset)

Rules & Constraints:
- Evaluates K using the Elbow Method (Inertia) & Silhouette Score.
- Selected K is configurable (default K=6).
- Serializes model using Python `pickle` (NO Joblib).
- Outputs cluster statistics, zone mapping, and visualization plots.
"""

import os
import json
import pickle
import argparse
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CANDIDATE_DATASET_PATHS = [
    os.path.join(BASE_DIR, "dataset", "mumbai_bmc_complaint_categorization_dataset_v2.csv"),
    os.path.join(BASE_DIR, "ml", "dataset", "mumbai_bmc_complaint_categorization_dataset_v2.csv"),
    os.path.join(BASE_DIR, "..", "dataset", "mumbai_bmc_complaint_categorization_dataset_v2.csv"),
]

def find_dataset():
    for p in CANDIDATE_DATASET_PATHS:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("Dataset CSV not found.")

ZONE_METADATA_PRESETS = {
    0: {"name": "Central Mumbai (Parel / Dadar / Wadala)", "color": "#2563EB"},
    1: {"name": "Western Suburbs (Andheri / Jogeshwari / Vile Parle)", "color": "#059669"},
    2: {"name": "Eastern Suburbs (Kurla / Chembur / Govandi)", "color": "#D97706"},
    3: {"name": "Northern Suburbs (Borivali / Kandivali / Dahisar)", "color": "#DC2626"},
    4: {"name": "North-Eastern Suburbs (Bhandup / Mulund)", "color": "#7C3AED"},
    5: {"name": "South Mumbai (Colaba / Fort / Marine Lines)", "color": "#DB2777"}
}

def train_clustering_model(selected_k: int = 6, run_elbow: bool = True):
    dataset_path = find_dataset()
    print(f"[*] Loading coordinates from: {dataset_path}")
    df = pd.read_csv(dataset_path)

    assert "latitude" in df.columns and "longitude" in df.columns, "Missing lat/lon columns"

    # Data validation: remove nulls and coordinates outside Mumbai bounds
    initial_count = len(df)
    coords_df = df.dropna(subset=["latitude", "longitude"]).copy()
    coords_df = coords_df[
        (coords_df["latitude"] >= 18.80) & (coords_df["latitude"] <= 19.40) &
        (coords_df["longitude"] >= 72.70) & (coords_df["longitude"] <= 73.10)
    ]
    valid_count = len(coords_df)
    print(f"[*] Total records: {initial_count} | Valid Mumbai geo-coordinates: {valid_count}")

    X = coords_df[["latitude", "longitude"]].values

    # Determine Number of Clusters: Elbow Method (Section 4)
    if run_elbow:
        print("\n" + "=" * 60)
        print("       DETERMINING K: ELBOW METHOD & SILHOUETTE ANALYSIS")
        print("=" * 60)
        k_range = range(2, 11)
        inertias = []
        sil_scores = []

        # Subsample for fast silhouette calculation
        sample_size = min(3000, len(X))
        np.random.seed(42)
        sample_indices = np.random.choice(len(X), sample_size, replace=False)
        X_sample = X[sample_indices]

        print(f"{'K':<5} | {'Inertia (SSE)':<18} | {'Silhouette Score':<18}")
        print("-" * 48)

        for k in k_range:
            km = KMeans(n_clusters=k, random_state=42, n_init=5)
            km.fit(X)
            inertias.append(km.inertia_)

            km_sample = KMeans(n_clusters=k, random_state=42, n_init=5)
            labels_sample = km_sample.fit_predict(X_sample)
            score = silhouette_score(X_sample, labels_sample)
            sil_scores.append(score)

            print(f"{k:<5} | {km.inertia_:<18.4f} | {score:<18.4f}")

        # Plot Elbow Curve
        plots_dir = os.path.join(BASE_DIR, "ml")
        os.makedirs(plots_dir, exist_ok=True)
        elbow_plot_path = os.path.join(plots_dir, "elbow_curve.png")

        fig, ax1 = plt.subplots(figsize=(8, 5))
        color = "tab:blue"
        ax1.set_xlabel("Number of Clusters (K)", fontweight="bold")
        ax1.set_ylabel("Inertia (Within-Cluster Sum of Squares)", color=color, fontweight="bold")
        ax1.plot(list(k_range), inertias, "bo-", linewidth=2, markersize=8, color=color, label="Inertia")
        ax1.tick_params(axis="y", labelcolor=color)
        ax1.grid(True, linestyle="--", alpha=0.5)

        ax2 = ax1.twinx()
        color = "tab:red"
        ax2.set_ylabel("Silhouette Score", color=color, fontweight="bold")
        ax2.plot(list(k_range), sil_scores, "rs--", linewidth=2, markersize=6, color=color, label="Silhouette Score")
        ax2.tick_params(axis="y", labelcolor=color)

        plt.title("Elbow Method & Silhouette Score for Optimal K (Mumbai Civic Complaints)", fontweight="bold", pad=12)
        fig.tight_layout()
        plt.savefig(elbow_plot_path, dpi=200)
        plt.close()
        print(f"[+] Saved Elbow Method plot to: {elbow_plot_path}")

    # Train Final K-Means Model
    print(f"\n[*] Training final K-Means model with selected K = {selected_k}...")
    kmeans = KMeans(n_clusters=selected_k, random_state=42, n_init=10)
    kmeans.fit(X)
    coords_df["cluster"] = kmeans.labels_

    # Calculate cluster statistics and representative metadata
    cluster_info_list = []
    print("\n[*] Hotspot Clusters Discovered from Mumbai Dataset:")
    print("-" * 75)

    for cid in range(selected_k):
        c_sub = coords_df[coords_df["cluster"] == cid]
        count = len(c_sub)
        pct = round((count / valid_count) * 100, 2)
        cen_lat, cen_lon = kmeans.cluster_centers_[cid]

        top_ward = c_sub["mumbai_ward"].mode()[0] if "mumbai_ward" in c_sub.columns and not c_sub["mumbai_ward"].mode().empty else "Ward"
        top_loc = c_sub["location"].mode()[0] if "location" in c_sub.columns and not c_sub["location"].mode().empty else "Mumbai"

        preset = ZONE_METADATA_PRESETS.get(cid, {
            "name": f"Cluster {cid + 1} ({top_loc.split(',')[0]} / Ward {top_ward})",
            "color": "#3B82F6"
        })

        info = {
            "cluster_id": cid,
            "zone_name": preset["name"],
            "centroid_latitude": round(float(cen_lat), 6),
            "centroid_longitude": round(float(cen_lon), 6),
            "complaint_count": int(count),
            "percentage": pct,
            "top_ward": str(top_ward),
            "top_location": str(top_loc),
            "color": preset["color"]
        }
        cluster_info_list.append(info)
        print(f"Cluster {cid}: {info['zone_name']}")
        print(f"   Centroid: ({cen_lat:.5f}, {cen_lon:.5f}) | Complaints: {count:,} ({pct}%) | Top Ward: {top_ward}")

    # Plot Cluster Scatter
    plots_dir = os.path.join(BASE_DIR, "ml")
    scatter_plot_path = os.path.join(plots_dir, "mumbai_hotspots_scatter.png")
    plt.figure(figsize=(9, 10))
    for cid in range(selected_k):
        c_sub = coords_df[coords_df["cluster"] == cid]
        info = cluster_info_list[cid]
        plt.scatter(
            c_sub["longitude"], c_sub["latitude"],
            s=4, alpha=0.35, color=info["color"], label=f"{info['zone_name']} (n={info['complaint_count']})"
        )
    # Plot centroids
    centers = kmeans.cluster_centers_
    plt.scatter(
        centers[:, 1], centers[:, 0],
        s=120, color="black", marker="X", edgecolors="white", linewidths=1.5, label="Cluster Centroids"
    )
    plt.xlabel("Longitude (°E)", fontweight="bold")
    plt.ylabel("Latitude (°N)", fontweight="bold")
    plt.title("Mumbai Civic Complaint Hotspots (K-Means Clustering)", fontweight="bold", pad=12)
    plt.legend(loc="upper left", fontsize=8, framealpha=0.9)
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(scatter_plot_path, dpi=200)
    plt.close()
    print(f"[+] Saved Hotspot Scatter plot to: {scatter_plot_path}")

    # Serialize Model & Info with Python pickle (NO Joblib!)
    target_dirs = [
        BASE_DIR,
        os.path.join(BASE_DIR, "ml"),
        os.path.join(BASE_DIR, "ml", "model")
    ]
    for d in target_dirs:
        os.makedirs(d, exist_ok=True)
        m_file = os.path.join(d, "kmeans_model.pkl")
        info_json = os.path.join(d, "kmeans_cluster_info.json")
        info_pkl = os.path.join(d, "kmeans_cluster_info.pkl")

        with open(m_file, "wb") as f:
            pickle.dump(kmeans, f, protocol=pickle.HIGHEST_PROTOCOL)

        with open(info_json, "w", encoding="utf-8") as f:
            json.dump(cluster_info_list, f, indent=2)

        with open(info_pkl, "wb") as f:
            pickle.dump(cluster_info_list, f, protocol=pickle.HIGHEST_PROTOCOL)

        print(f"[+] Saved K-Means pickled model and cluster metadata to: {d}")

    print("\n[SUCCESS] Hotspot Clustering Model Training Complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train K-Means Hotspot Model")
    parser.add_argument("--k", type=int, default=6, help="Configurable number of clusters K (default: 6)")
    parser.add_argument("--skip-elbow", action="store_true", help="Skip elbow calculation")
    args = parser.parse_args()

    train_clustering_model(selected_k=args.k, run_elbow=not args.skip_elbow)
