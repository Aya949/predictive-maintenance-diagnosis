"""
Step 4 — Diagnostic Reasoning Engine.
Identifies the physical phenomenon behind the combination of interpreted features.
"""

from apps.Knowledge.rules import match_pattern


def diagnose_phenomenon(interpreted_features, predicted_class):
    phenomenon_id = match_pattern(interpreted_features, predicted_class)
    return {
        'phenomenon_id': phenomenon_id,
        'based_on': [f['feature'] for f in interpreted_features],
    }