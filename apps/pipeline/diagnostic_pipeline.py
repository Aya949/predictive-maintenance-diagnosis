"""
Orchestrates the full Engineering Diagnostic Reasoning Engine, Steps 1-6.
"""

from apps.models.predictor import FaultPredictor
from apps.explainability.shap_explainer import ShapExplainer
from apps.explainability.feature_interpreter import interpret_features
from apps.explainability.reasoning_engine import diagnose_phenomenon
from apps.explainability.root_cause import get_root_causes
from apps.explainability.maintenance import recommend_actions
from apps.explainability.report_generator import generate_report


class DiagnosticEngine:
    def __init__(self, background_data, feature_cols):
        self.predictor = FaultPredictor()
        self.shap_explainer = ShapExplainer(self.predictor.model, background_data)
        self.feature_cols = feature_cols

    def diagnose(self, feature_vector: dict, top_n=5, as_report=False):
        # Step 1 — Fault Prediction
        pred_result = self.predictor.predict(feature_vector, self.feature_cols)
        predicted_idx = list(self.predictor.label_encoder.classes_).index(pred_result['predicted_class'])

        # Step 2 — SHAP Explainability
        top_shap = self.shap_explainer.explain(
            pred_result['input_tensor'], self.feature_cols, predicted_idx, top_n
        )

        # Step 3 — Engineering Feature Interpretation
        interpreted = interpret_features(top_shap)

        # Step 4 — Diagnostic Reasoning Engine
        phenomenon = diagnose_phenomenon(interpreted, pred_result['predicted_class'])

        # Step 5 — Root Cause Analysis
        root_causes = get_root_causes(phenomenon['phenomenon_id'])

        # Step 6 — Maintenance Decision Support
        recommendations = recommend_actions(root_causes)

        result = {
            'predicted_class': pred_result['predicted_class'],
            'confidence': pred_result['confidence'],
            'top_features': interpreted,
            'phenomenon': phenomenon,
            'root_causes': recommendations,
        }

        if as_report:
            return generate_report(result)

        return result