"""
Step 1 — Fault Prediction.
Wraps the trained neural network to produce a fault prediction
from a raw (unscaled) feature vector.
"""

import os

import joblib
import numpy as np
import pandas as pd
import torch

from apps.models.model_def import FaultDiagnosisNet

# Build paths relative to THIS file's location, not the working directory
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class FaultPredictor:
    def __init__(self,
                 model_path=None,
                 scaler_path=None,
                 label_encoder_path=None,
                 device='cpu'):

        model_path = model_path or os.path.join(_THIS_DIR, 'fault_diagnosis_model.pth')
        scaler_path = scaler_path or os.path.join(_THIS_DIR, 'scaler.pkl')
        label_encoder_path = label_encoder_path or os.path.join(_THIS_DIR, 'label_encoder.pkl')

        self.device = torch.device(device)
        self.scaler = joblib.load(scaler_path)
        self.label_encoder = joblib.load(label_encoder_path)

        num_classes = len(self.label_encoder.classes_)
        input_size = self.scaler.n_features_in_

        self.model = FaultDiagnosisNet(input_size=input_size, num_classes=num_classes)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()

    def predict(self, feature_vector: dict, feature_cols: list):
        ordered_values = pd.DataFrame(
            [[feature_vector[col] for col in feature_cols]],
            columns=feature_cols,
        )
        scaled = self.scaler.transform(ordered_values)

        with torch.no_grad():
            input_tensor = torch.tensor(scaled, dtype=torch.float32).to(self.device)
            logits = self.model(input_tensor)
            probs = torch.softmax(logits, dim=1)
            pred_idx = torch.argmax(probs, dim=1).item()
            confidence = probs[0][pred_idx].item()

        predicted_class = self.label_encoder.classes_[pred_idx]
        raw_probabilities = {
            cls: float(probs[0][i].item())
            for i, cls in enumerate(self.label_encoder.classes_)
        }

        return {
            'predicted_class': predicted_class,
            'confidence': confidence,
            'raw_probabilities': raw_probabilities,
            'scaled_input': scaled,
            'input_tensor': input_tensor,
        }