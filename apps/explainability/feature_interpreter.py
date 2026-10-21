"""
Step 3 — Engineering Feature Interpretation.
Translates SHAP's top features into physical categories and plain-language meaning.
"""

from apps.knowledge.feature_knowledge import categorize_feature, describe_feature


def interpret_features(top_shap_features):
    """
    top_shap_features: output of ShapExplainer.explain() — list of dicts
    Returns: same list, enriched with category + physical description
    """
    interpreted = []
    for f in top_shap_features:
        channel_cat, stat_cat = categorize_feature(f['feature'])
        interpreted.append({
            **f,
            'channel_category': channel_cat,
            'stat_category': stat_cat,
            'meaning': describe_feature(f['feature']),
        })
    return interpreted