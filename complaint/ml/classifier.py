import os
import pickle
import re
from typing import Dict, Any, Tuple

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")

VECTORIZER_PATH = os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl")
if not os.path.exists(VECTORIZER_PATH):
    VECTORIZER_PATH = os.path.join(os.path.dirname(BASE_DIR), "tfidf_vectorizer.pkl")

CLASSIFIER_PATH = os.path.join(MODEL_DIR, "complaint_classifier.pkl")
if not os.path.exists(CLASSIFIER_PATH):
    CLASSIFIER_PATH = os.path.join(os.path.dirname(BASE_DIR), "complaint_classifier.pkl")

# Centralized Department Mapping
CATEGORY_TO_DEPARTMENT = {
    "Water Supply": {
        "department_code": "WATER",
        "department_name": "Water Department",
        "default_priority": "MEDIUM"
    },
    "Electricity": {
        "department_code": "ELECTRICITY",
        "department_name": "Electricity Department",
        "default_priority": "HIGH"
    },
    "Street Lighting": {
        "department_code": "ELECTRICITY",
        "department_name": "Electricity Department",
        "default_priority": "MEDIUM"
    },
    "Roads & Footpaths": {
        "department_code": "ROADS",
        "department_name": "Roads & Infrastructure Department",
        "default_priority": "MEDIUM"
    },
    "Solid Waste Management": {
        "department_code": "WASTE",
        "department_name": "Waste Management Department",
        "default_priority": "MEDIUM"
    },
    "Public Toilets & Sanitation": {
        "department_code": "WASTE",
        "department_name": "Waste Management Department",
        "default_priority": "MEDIUM"
    },
    "Drainage & Sewerage": {
        "department_code": "DRAINAGE",
        "department_name": "Drainage Department",
        "default_priority": "HIGH"
    },
    "Stormwater & Flooding": {
        "department_code": "DRAINAGE",
        "department_name": "Drainage Department",
        "default_priority": "HIGH"
    },
    "Traffic & Road Safety": {
        "department_code": "TRAFFIC",
        "department_name": "Traffic Department",
        "default_priority": "HIGH"
    },
    "Public Transport": {
        "department_code": "TRAFFIC",
        "department_name": "Traffic Department",
        "default_priority": "MEDIUM"
    },
    "Public Safety & Security": {
        "department_code": "PUBLIC_SAFETY",
        "department_name": "Public Safety Department",
        "default_priority": "HIGH"
    },
    "Animal Management": {
        "department_code": "PUBLIC_SAFETY",
        "department_name": "Public Safety Department",
        "default_priority": "LOW"
    },
    "Pollution": {
        "department_code": "HEALTHCARE",
        "department_name": "Healthcare & Environment Department",
        "default_priority": "MEDIUM"
    },
    "Trees & Gardens": {
        "department_code": "ROADS",
        "department_name": "Roads & Infrastructure Department",
        "default_priority": "LOW"
    },
    "Other Civic Services": {
        "department_code": "GENERAL",
        "department_name": "General Civic Department",
        "default_priority": "LOW"
    },
}

DEFAULT_DEPARTMENT = {
    "department_code": "GENERAL",
    "department_name": "General Civic Department",
    "default_priority": "LOW"
}

HIGH_SEVERITY_KEYWORDS = [
    "emergency", "danger", "burst", "electrocution", "sparking", "shock", "hazard", 
    "life", "accident", "fatal", "deep pothole", "flooded", "sewage overflowing",
    "fire", "collapse", "gas leak", "poison", "critical", "children"
]

class ComplaintClassifier:
    def __init__(self):
        self.vectorizer = None
        self.model = None
        self.is_loaded = False
        self.load_models()

    def load_models(self):
        try:
            if os.path.exists(VECTORIZER_PATH) and os.path.exists(CLASSIFIER_PATH):
                with open(VECTORIZER_PATH, "rb") as f:
                    self.vectorizer = pickle.load(f)
                with open(CLASSIFIER_PATH, "rb") as f:
                    self.model = pickle.load(f)
                self.is_loaded = True
                print(f"[UrbanSync ML] Models loaded successfully from {MODEL_DIR}")
            else:
                print(f"[UrbanSync ML] Warning: Model files not found at {VECTORIZER_PATH} or {CLASSIFIER_PATH}")
        except Exception as e:
            print(f"[UrbanSync ML] Error loading model: {e}")
            self.is_loaded = False

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def calculate_priority(self, text: str, predicted_category: str, citizen_impact: str) -> str:
        """
        Calculate final priority based on impact level + category + severity keywords
        """
        text_lower = text.lower()
        has_high_severity = any(kw in text_lower for kw in HIGH_SEVERITY_KEYWORDS)

        dept_info = CATEGORY_TO_DEPARTMENT.get(predicted_category, DEFAULT_DEPARTMENT)
        base_priority = dept_info.get("default_priority", "MEDIUM")

        if citizen_impact == "EMERGENCY" or has_high_severity:
            return "EMERGENCY"
        
        if citizen_impact == "HIGH":
            return "HIGH"
        elif citizen_impact == "MEDIUM":
            return "HIGH" if base_priority == "HIGH" else "MEDIUM"
        else: # LOW
            return base_priority

    def predict(self, title: str, description: str, citizen_impact: str = "MEDIUM") -> Dict[str, Any]:
        """
        Classifies the complaint and returns category, confidence, department, routing, and priority
        """
        full_text = f"{title}. {description}".strip()
        cleaned = self.clean_text(full_text)

        if not self.is_loaded or not cleaned:
            # Fallback rule-based or general civic if model is not loaded
            return {
                "category": "Other Civic Services",
                "subcategory": "General Issue",
                "confidence": 0.40,
                "department_code": "GENERAL",
                "department_name": "General Civic Department",
                "priority": citizen_impact or "LOW",
                "status": "UNCLASSIFIED",
                "routing_reason": "ML model unavailable or text insufficient. Sent to manual review."
            }

        try:
            features = self.vectorizer.transform([cleaned])
            pred_category = self.model.predict(features)[0]
            probabilities = self.model.predict_proba(features)[0]
            confidence = float(max(probabilities))

            dept_info = CATEGORY_TO_DEPARTMENT.get(pred_category, DEFAULT_DEPARTMENT)
            dept_code = dept_info["department_code"]
            dept_name = dept_info["department_name"]

            # Subcategory extraction
            subcategory = f"{pred_category} Issue"
            if "leak" in cleaned or "pipe" in cleaned:
                subcategory = "Pipeline Leakage"
            elif "pothole" in cleaned or "crater" in cleaned:
                subcategory = "Pothole & Surface Damage"
            elif "garbage" in cleaned or "dump" in cleaned:
                subcategory = "Uncollected Garbage"
            elif "light" in cleaned or "dark" in cleaned:
                subcategory = "Street Light Malfunction"
            elif "drain" in cleaned or "sewer" in cleaned or "clog" in cleaned:
                subcategory = "Drainage Overflow"
            elif "signal" in cleaned or "traffic" in cleaned:
                subcategory = "Traffic Signal Issue"

            # Threshold handling according to specification:
            # confidence >= 0.75: ASSIGNED
            # 0.50 <= confidence < 0.75: NEEDS_REVIEW
            # confidence < 0.50: UNCLASSIFIED
            if confidence >= 0.75:
                status = "ASSIGNED"
                routing_reason = f"High confidence ({round(confidence*100, 1)}%) automated assignment to {dept_name}."
            elif confidence >= 0.50:
                status = "NEEDS_REVIEW"
                routing_reason = f"Moderate confidence ({round(confidence*100, 1)}%). Routed to review queue for confirmation."
            else:
                status = "UNCLASSIFIED"
                dept_code = "GENERAL"
                dept_name = "General Civic Department"
                routing_reason = f"Low confidence ({round(confidence*100, 1)}%). Routed to Super Admin manual review."

            priority = self.calculate_priority(full_text, pred_category, citizen_impact)

            return {
                "category": pred_category,
                "subcategory": subcategory,
                "confidence": round(confidence, 4),
                "department_code": dept_code,
                "department_name": dept_name,
                "priority": priority,
                "status": status,
                "routing_reason": routing_reason
            }
        except Exception as e:
            print(f"[UrbanSync ML] Classification error: {e}")
            return {
                "category": "Other Civic Services",
                "subcategory": "General Issue",
                "confidence": 0.30,
                "department_code": "GENERAL",
                "department_name": "General Civic Department",
                "priority": citizen_impact or "LOW",
                "status": "UNCLASSIFIED",
                "routing_reason": f"Prediction exception occurred: {str(e)}"
            }

    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Calculates cosine similarity between two texts using the TF-IDF vectorizer
        """
        if not self.is_loaded:
            # Simple Jaccard similarity fallback
            w1 = set(self.clean_text(text1).split())
            w2 = set(self.clean_text(text2).split())
            if not w1 or not w2:
                return 0.0
            return len(w1.intersection(w2)) / len(w1.union(w2))

        try:
            from sklearn.metrics.pairwise import cosine_similarity
            f1 = self.vectorizer.transform([self.clean_text(text1)])
            f2 = self.vectorizer.transform([self.clean_text(text2)])
            sim = cosine_similarity(f1, f2)[0][0]
            return float(sim)
        except Exception:
            return 0.0

# Singleton instance
classifier_instance = ComplaintClassifier()
