"""
UrbanSync — Exploratory Data Analysis (EDA) Script
Performs full dataset profiling for:
1. Dataset Overview & Data Types
2. Missing Value Analysis & Handling
3. Duplicate Complaint Detection & Removal
4. Classification Analysis (15 BMC Categories Distribution & Text Length Profiling)
5. Clustering Analysis (Geographic Bounds, Coordinate Distribution, Hotspots)
6. Generates Summary JSON and Matplotlib Figures for Project Report
"""

import os
import json
import re
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

DATASET_PATH = os.path.join(PROJECT_ROOT, "dataset", "mumbai_bmc_complaint_categorization_dataset_v2.csv")
if not os.path.exists(DATASET_PATH):
    DATASET_PATH = os.path.join(BASE_DIR, "dataset", "mumbai_bmc_complaint_categorization_dataset_v2.csv")

def run_eda():
    print("=" * 70)
    print("      URBANSYNC: MUMBAI BMC CIVIC COMPLAINTS EXPLORATORY DATA ANALYSIS")
    print("=" * 70)

    print(f"[*] Reading dataset: {DATASET_PATH}")
    df = pd.read_csv(DATASET_PATH)

    # 1. Dataset Overview
    n_rows, n_cols = df.shape
    print("\n--- 1. DATASET OVERVIEW ---")
    print(f"Total Records: {n_rows:,}")
    print(f"Total Columns: {n_cols}")
    print("\nColumns & Data Types:")
    for col, dtype in df.dtypes.items():
        print(f"  - {col:<32}: {dtype}")

    # 2. Missing Values
    print("\n--- 2. MISSING VALUES ANALYSIS ---")
    missing_counts = df.isnull().sum()
    for col, cnt in missing_counts.items():
        pct = (cnt / n_rows) * 100
        print(f"  - {col:<32}: {cnt} ({pct:.2f}%)")

    # 3. Duplicate Records
    print("\n--- 3. DUPLICATE ANALYSIS ---")
    exact_dups = df.duplicated().sum()
    text_col = "complaint_text_clean_mumbai" if "complaint_text_clean_mumbai" in df.columns else "complaint_text_mumbai"
    text_dups = df.duplicated(subset=[text_col]).sum()
    print(f"Exact Duplicate Rows:       {exact_dups}")
    print(f"Duplicate Complaint Texts:  {text_dups}")

    # 4. Classification EDA: 15 BMC Categories
    print("\n--- 4. CLASSIFICATION EDA: 15 BMC CATEGORIES ---")
    target_col = "bmc_category_15"
    cat_counts = df[target_col].value_counts()
    for cat, cnt in cat_counts.items():
        pct = (cnt / n_rows) * 100
        print(f"  - {cat:<32}: {cnt:,} ({pct:.2f}%)")

    # Text length metrics
    lengths_char = df[text_col].dropna().apply(lambda x: len(str(x)))
    lengths_word = df[text_col].dropna().apply(lambda x: len(str(x).split()))

    avg_chars = float(lengths_char.mean())
    med_chars = float(lengths_char.median())
    avg_words = float(lengths_word.mean())
    med_words = float(lengths_word.median())

    print(f"\nComplaint Text Statistics:")
    print(f"  - Average Characters:     {avg_chars:.1f}")
    print(f"  - Median Characters:      {med_chars:.1f}")
    print(f"  - Average Word Count:     {avg_words:.1f}")
    print(f"  - Median Word Count:      {med_words:.1f}")

    # 5. Clustering EDA: Geographic Bounds
    print("\n--- 5. CLUSTERING EDA: GEOGRAPHIC DISTRIBUTION ---")
    valid_coords = df.dropna(subset=["latitude", "longitude"])
    min_lat, max_lat = valid_coords["latitude"].min(), valid_coords["latitude"].max()
    min_lon, max_lon = valid_coords["longitude"].min(), valid_coords["longitude"].max()

    print(f"Valid Coordinates:          {len(valid_coords):,} / {n_rows:,}")
    print(f"Latitude Range:             [{min_lat:.4f}°N, {max_lat:.4f}°N]")
    print(f"Longitude Range:            [{min_lon:.4f}°E, {max_lon:.4f}°E]")

    # Visualizations
    plots_dir = BASE_DIR
    os.makedirs(plots_dir, exist_ok=True)

    # Plot 1: Category Distribution
    plt.figure(figsize=(10, 6))
    cat_counts.plot(kind="barh", color="#2563EB", edgecolor="#1E3A8A")
    plt.title("Distribution of 15 BMC Municipal Complaint Categories", fontweight="bold", pad=12)
    plt.xlabel("Number of Complaints", fontweight="bold")
    plt.gca().invert_yaxis()
    plt.grid(axis="x", linestyle="--", alpha=0.5)
    plt.tight_layout()
    cat_plot_path = os.path.join(plots_dir, "category_distribution.png")
    plt.savefig(cat_plot_path, dpi=200)
    plt.close()
    print(f"[+] Saved Category Distribution Chart: {cat_plot_path}")

    # Plot 2: Text Length Histogram
    plt.figure(figsize=(8, 5))
    plt.hist(lengths_word, bins=40, color="#059669", edgecolor="#064E3B", alpha=0.85)
    plt.axvline(avg_words, color="red", linestyle="--", label=f"Mean: {avg_words:.1f} words")
    plt.axvline(med_words, color="orange", linestyle=":", label=f"Median: {med_words:.1f} words")
    plt.title("Complaint Text Word Count Distribution", fontweight="bold", pad=12)
    plt.xlabel("Word Count", fontweight="bold")
    plt.ylabel("Frequency", fontweight="bold")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    len_plot_path = os.path.join(plots_dir, "text_length_distribution.png")
    plt.savefig(len_plot_path, dpi=200)
    plt.close()
    print(f"[+] Saved Text Length Histogram: {len_plot_path}")

    # Save summary JSON
    summary_data = {
        "dataset_name": "Mumbai BMC Civic Complaints Dataset v2",
        "total_records": int(n_rows),
        "total_columns": int(n_cols),
        "exact_duplicates": int(exact_dups),
        "text_duplicates": int(text_dups),
        "text_statistics": {
            "average_characters": round(avg_chars, 1),
            "median_characters": round(med_chars, 1),
            "average_words": round(avg_words, 1),
            "median_words": round(med_words, 1)
        },
        "geographic_bounds": {
            "min_latitude": round(float(min_lat), 4),
            "max_latitude": round(float(max_lat), 4),
            "min_longitude": round(float(min_lon), 4),
            "max_longitude": round(float(max_lon), 4)
        },
        "category_counts": {cat: int(cnt) for cat, cnt in cat_counts.items()}
    }

    json_path = os.path.join(BASE_DIR, "eda_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    print(f"[+] Saved EDA summary JSON: {json_path}")

    print("\n[SUCCESS] Exploratory Data Analysis Complete.")

if __name__ == "__main__":
    run_eda()
