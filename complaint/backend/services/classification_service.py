import os
import re
import pickle
from typing import Dict, Any

# Model paths resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

CANDIDATE_VEC_PATHS = [
    os.path.join(PROJECT_ROOT, "tfidf_vectorizer.pkl"),
    os.path.join(PROJECT_ROOT, "ml", "tfidf_vectorizer.pkl"),
    os.path.join(PROJECT_ROOT, "ml", "model", "tfidf_vectorizer.pkl"),
    os.path.join(BASE_DIR, "..", "ml", "tfidf_vectorizer.pkl")
]

CANDIDATE_CLF_PATHS = [
    os.path.join(PROJECT_ROOT, "complaint_classifier.pkl"),
    os.path.join(PROJECT_ROOT, "ml", "complaint_classifier.pkl"),
    os.path.join(PROJECT_ROOT, "ml", "model", "complaint_classifier.pkl"),
    os.path.join(BASE_DIR, "..", "ml", "complaint_classifier.pkl")
]

def find_file(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return paths[0]

# BMC 15 Categories Mapping to Municipal Departments
BMC_CATEGORY_MAPPING = {
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
    "Traffic & Road Safety": {
        "department_code": "TRAFFIC",
        "department_name": "Traffic Department",
        "default_priority": "HIGH"
    },
    "Street Lighting": {
        "department_code": "ELECTRICITY",
        "department_name": "Electricity Department",
        "default_priority": "MEDIUM"
    },
    "Trees & Gardens": {
        "department_code": "ROADS",
        "department_name": "Roads & Infrastructure Department",
        "default_priority": "LOW"
    },
    "Drainage & Sewerage": {
        "department_code": "DRAINAGE",
        "department_name": "Drainage Department",
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
    "Public Toilets & Sanitation": {
        "department_code": "WASTE",
        "department_name": "Waste Management Department",
        "default_priority": "MEDIUM"
    },
    "Water Supply": {
        "department_code": "WATER",
        "department_name": "Water Department",
        "default_priority": "HIGH"
    },
    "Electricity": {
        "department_code": "ELECTRICITY",
        "department_name": "Electricity Department",
        "default_priority": "HIGH"
    },
    "Other Civic Services": {
        "department_code": "GENERAL",
        "department_name": "General Civic Department",
        "default_priority": "LOW"
    },
    "Stormwater & Flooding": {
        "department_code": "DRAINAGE",
        "department_name": "Drainage Department",
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
    }
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

class ClassificationService:
    def __init__(self):
        self.vectorizer = None
        self.classifier = None
        self.is_loaded = False
        self.load_models()

    def load_models(self):
        """Loads TF-IDF vectorizer and Logistic Regression model using pickle."""
        vec_path = find_file(CANDIDATE_VEC_PATHS)
        clf_path = find_file(CANDIDATE_CLF_PATHS)

        try:
            if os.path.exists(vec_path) and os.path.exists(clf_path):
                with open(vec_path, "rb") as f:
                    self.vectorizer = pickle.load(f)
                with open(clf_path, "rb") as f:
                    self.classifier = pickle.load(f)
                self.is_loaded = True
                print(f"[ClassificationService] Pickled models loaded successfully from:\n  - {vec_path}\n  - {clf_path}")
            else:
                print(f"[ClassificationService] Warning: Pickled model files not found. Run train_classification.py first.")
                self.is_loaded = False
        except Exception as e:
            print(f"[ClassificationService] Error loading pickled models: {e}")
            self.is_loaded = False

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Reproducible text cleaning:
        - Handle missing values
        - Lowercase
        - Remove URLs and HTML tags
        - Remove special characters
        - Normalize whitespace
        """
        if not text:
            return ""
        text = str(text).lower().strip()
        text = re.sub(r"https?://\S+|www\.\S+", " ", text)
        text = re.sub(r"<.*?>", " ", text)
        text = re.sub(r"&[a-z]+;", " ", text)
        text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def calculate_priority(self, text: str, predicted_category: str, citizen_impact: str) -> str:
        text_lower = text.lower()
        has_high_severity = any(kw in text_lower for kw in HIGH_SEVERITY_KEYWORDS)
        dept_info = BMC_CATEGORY_MAPPING.get(predicted_category, DEFAULT_DEPARTMENT)
        base_priority = dept_info.get("default_priority", "MEDIUM")

        if citizen_impact == "EMERGENCY" or has_high_severity:
            return "EMERGENCY"
        if citizen_impact == "HIGH":
            return "HIGH"
        elif citizen_impact == "MEDIUM":
            return "HIGH" if base_priority == "HIGH" else "MEDIUM"
        else:
            return base_priority

    def classify_complaint(self, text: str, citizen_impact: str = "MEDIUM") -> Dict[str, Any]:
        """
        Takes raw complaint description, cleans it, vectors via TF-IDF,
        predicts BMC category via Logistic Regression, and maps to department.
        NOTE: Confidence is stored internally for routing/triaging,
        but NOT displayed to citizens per requirements.
        """
        cleaned = self.clean_text(text)

        if not self.is_loaded or not cleaned:
            return {
                "category": "Other Civic Services",
                "subcategory": "General Issue",
                "confidence": 0.40,
                "department_code": "GENERAL",
                "department_name": "General Civic Department",
                "priority": citizen_impact or "LOW",
                "status": "UNCLASSIFIED",
                "routing_reason": "Automatic categorization unavailable or text insufficient."
            }

        try:
            features = self.vectorizer.transform([cleaned])
            pred_category = self.classifier.predict(features)[0]
            probabilities = self.classifier.predict_proba(features)[0]
            confidence = float(max(probabilities))

            dept_info = BMC_CATEGORY_MAPPING.get(pred_category, DEFAULT_DEPARTMENT)
            dept_code = dept_info["department_code"]
            dept_name = dept_info["department_name"]

            # Subcategory extraction for detail view
            subcategory = f"{pred_category} Issue"
            if "leak" in cleaned or "pipe" in cleaned or "burst" in cleaned:
                subcategory = "Pipeline Leakage"
            elif "pothole" in cleaned or "crater" in cleaned or "tar" in cleaned:
                subcategory = "Pothole & Surface Damage"
            elif "garbage" in cleaned or "dump" in cleaned or "waste" in cleaned or "bin" in cleaned:
                subcategory = "Uncollected Garbage"
            elif "light" in cleaned or "dark" in cleaned or "pole" in cleaned:
                subcategory = "Street Light Malfunction"
            elif "drain" in cleaned or "sewer" in cleaned or "clog" in cleaned:
                subcategory = "Drainage Overflow"
            elif "signal" in cleaned or "traffic" in cleaned or "jam" in cleaned:
                subcategory = "Traffic Signal Issue"
            elif "water" in cleaned:
                subcategory = "Water Supply Disruption"

            if confidence >= 0.70:
                status = "ASSIGNED"
                routing_reason = f"High confidence automated assignment to {dept_name}."
            elif confidence >= 0.45:
                status = "NEEDS_REVIEW"
                routing_reason = f"Moderate confidence. Assigned to {dept_name} queue with review flag."
            else:
                status = "UNCLASSIFIED"
                dept_code = "GENERAL"
                dept_name = "General Civic Department"
                routing_reason = "Low confidence prediction. Routed to Super Admin review."

            priority = self.calculate_priority(text, pred_category, citizen_impact)

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
            print(f"[ClassificationService] Prediction error: {e}")
            return {
                "category": "Other Civic Services",
                "subcategory": "General Issue",
                "confidence": 0.30,
                "department_code": "GENERAL",
                "department_name": "General Civic Department",
                "priority": citizen_impact or "LOW",
                "status": "UNCLASSIFIED",
                "routing_reason": f"Prediction error: {str(e)}"
            }

classification_service = ClassificationService()
