"""
UrbanSync ML Subpackage Training Entrypoint
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from train_classification import train_classification_model

if __name__ == "__main__":
    train_classification_model()
