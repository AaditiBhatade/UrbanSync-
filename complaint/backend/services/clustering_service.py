import os
import json
import pickle
from typing import Optional, Tuple, Dict, Any, List

# Model paths resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

CANDIDATE_KM_PATHS = [
    os.path.join(PROJECT_ROOT, "kmeans_model.pkl"),
    os.path.join(PROJECT_ROOT, "ml", "kmeans_model.pkl"),
    os.path.join(PROJECT_ROOT, "ml", "model", "kmeans_model.pkl"),
    os.path.join(BASE_DIR, "..", "ml", "kmeans_model.pkl")
]

CANDIDATE_INFO_PATHS = [
    os.path.join(PROJECT_ROOT, "kmeans_cluster_info.json"),
    os.path.join(PROJECT_ROOT, "ml", "kmeans_cluster_info.json"),
    os.path.join(PROJECT_ROOT, "ml", "model", "kmeans_cluster_info.json"),
    os.path.join(BASE_DIR, "..", "ml", "kmeans_cluster_info.json")
]

def find_file(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return paths[0]

# Default fallback clusters if info file is missing
DEFAULT_CLUSTERS = [
    {"cluster_id": 0, "zone_name": "Central Mumbai (Parel / Dadar / Wadala)", "centroid_latitude": 19.00199, "centroid_longitude": 72.836203, "complaint_count": 3332, "color": "#2563EB"},
    {"cluster_id": 1, "zone_name": "Western Suburbs (Andheri / Jogeshwari / Vile Parle)", "centroid_latitude": 19.147346, "centroid_longitude": 72.850029, "complaint_count": 2732, "color": "#059669"},
    {"cluster_id": 2, "zone_name": "Eastern Suburbs (Kurla / Chembur / Govandi)", "centroid_latitude": 19.068084, "centroid_longitude": 72.883398, "complaint_count": 3940, "color": "#D97706"},
    {"cluster_id": 3, "zone_name": "Northern Suburbs (Borivali / Kandivali / Dahisar)", "centroid_latitude": 19.227093, "centroid_longitude": 72.853677, "complaint_count": 1961, "color": "#DC2626"},
    {"cluster_id": 4, "zone_name": "North-Eastern Suburbs (Bhandup / Mulund)", "centroid_latitude": 19.154793, "centroid_longitude": 72.949862, "complaint_count": 1306, "color": "#7C3AED"},
    {"cluster_id": 5, "zone_name": "South Mumbai (Colaba / Fort / Marine Lines)", "centroid_latitude": 18.942055, "centroid_longitude": 72.817287, "complaint_count": 2735, "color": "#DB2777"}
]

class ClusteringService:
    def __init__(self):
        self.kmeans_model = None
        self.cluster_metadata: List[Dict[str, Any]] = []
        self.is_loaded = False
        self.load_model()

    def load_model(self):
        """Loads pickled K-Means model and cluster zone metadata."""
        km_path = find_file(CANDIDATE_KM_PATHS)
        info_path = find_file(CANDIDATE_INFO_PATHS)

        try:
            if os.path.exists(km_path):
                with open(km_path, "rb") as f:
                    self.kmeans_model = pickle.load(f)
                self.is_loaded = True
                print(f"[ClusteringService] K-Means model loaded successfully from: {km_path}")
            else:
                print(f"[ClusteringService] Warning: kmeans_model.pkl not found at {km_path}")

            if os.path.exists(info_path):
                with open(info_path, "r", encoding="utf-8") as f:
                    self.cluster_metadata = json.load(f)
            else:
                self.cluster_metadata = DEFAULT_CLUSTERS
        except Exception as e:
            print(f"[ClusteringService] Error loading clustering model: {e}")
            self.kmeans_model = None
            self.is_loaded = False
            self.cluster_metadata = DEFAULT_CLUSTERS

    @staticmethod
    def is_valid_mumbai_coordinate(lat: Optional[float], lon: Optional[float]) -> bool:
        if lat is None or lon is None:
            return False
        # Mumbai bounding box
        return (18.70 <= lat <= 19.45) and (72.65 <= lon <= 73.20)

    def predict_cluster(self, lat: Optional[float], lon: Optional[float]) -> Tuple[Optional[int], str]:
        """
        Receives latitude and longitude.
        Loads the K-Means model.
        Predicts the cluster.
        Returns (cluster_id, zone_name).
        """
        if lat is None or lon is None:
            return None, "Location not specified"

        if not self.is_loaded or self.kmeans_model is None:
            return None, "Hotspot clustering uninitialized"

        try:
            # Predict cluster using latitude, longitude
            cluster_idx = int(self.kmeans_model.predict([[float(lat), float(lon)]])[0])
            
            zone_name = f"Hotspot Cluster {cluster_idx + 1}"
            for c in self.cluster_metadata:
                if c.get("cluster_id") == cluster_idx:
                    zone_name = c.get("zone_name", zone_name)
                    break

            return cluster_idx, zone_name
        except Exception as e:
            print(f"[ClusteringService] Cluster prediction error: {e}")
            return None, f"Clustering error: {str(e)}"

    def get_all_hotspots(self) -> List[Dict[str, Any]]:
        """Returns all 6 K-Means hotspots with details for map visualization and table."""
        if self.cluster_metadata:
            return self.cluster_metadata
        return DEFAULT_CLUSTERS

clustering_service = ClusteringService()
