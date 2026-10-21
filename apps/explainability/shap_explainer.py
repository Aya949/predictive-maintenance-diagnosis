"""
Step 2 — SHAP Explainability.
Computes which features drove a specific prediction.
"""

import numpy as np
import shap
import torch


class ShapExplainer:
    def __init__(self, model, background_data, device='cpu'):
        self.device = torch.device(device)
        self.model = model
        background_tensor = torch.tensor(background_data, dtype=torch.float32).to(self.device)
        self.explainer = shap.GradientExplainer(self.model, background_tensor)

    def explain(self, input_tensor, feature_cols, predicted_class_idx, top_n=5):
        shap_values = self.explainer.shap_values(input_tensor)
        sample_shap = shap_values[0, :, predicted_class_idx]
        ranked_idx = np.argsort(np.abs(sample_shap))[::-1][:top_n]

        top_features = []
        for i in ranked_idx:
            top_features.append({
                'feature': feature_cols[i],
                'shap_value': float(sample_shap[i]),
                'direction': 'increases' if sample_shap[i] > 0 else 'decreases',
            })
        return top_features