"""
Diagnostic pattern rules: combinations of feature categories -> physical phenomenon.
"""

def match_pattern(interpreted_features, predicted_class):
    channel_cats = set(f['channel_category'] for f in interpreted_features)
    stat_cats = set(f['stat_category'] for f in interpreted_features)

    if predicted_class in ('underhang_bearing', 'overhang_bearing'):
        if 'impact_signature' in stat_cats and 'acoustic' in channel_cats:
            return "impact_damage_confirmed"
        elif 'impact_signature' in stat_cats:
            return "impact_damage_early"
        elif 'energy_level' in stat_cats or 'general_roughness' in stat_cats:
            return "wear_or_lubrication"
        elif 'peak_magnitude' in stat_cats and 'waveform_shape' not in stat_cats:
            return "clearance_or_looseness"
        elif 'waveform_shape' in stat_cats or 'asymmetry' in stat_cats:
            return "uneven_load_wear"

    if predicted_class == 'imbalance':
        if 'baseline_level' in stat_cats or 'general_roughness' in stat_cats:
            return "mass_imbalance"

    if predicted_class in ('horizontal_misalignment', 'vertical_misalignment'):
        return "shaft_misalignment"

    if predicted_class == 'normal':
        return "healthy_operation"

    return "unmatched_pattern"