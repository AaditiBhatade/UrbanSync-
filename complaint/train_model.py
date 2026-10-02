"""
UrbanSync — Master Machine Learning Training Entrypoint
Runs Model Training for:
1. Classification: TF-IDF + Logistic Regression
"""

import sys
import os

# Add root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from train_classification import train_classification_model

if __name__ == "__main__":
    print("=================================================================")
    print("  URBANSYNC: TRAINING CLASSIFICATION MODEL (TF-IDF + LOGISTIC REGRESSION)")
    print("=================================================================")
    train_classification_model()
