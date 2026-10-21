"""
Knowledge base: physical meaning of each channel and statistic.
"""

CHANNEL_CATEGORY = {
    'tachometer': 'speed',
    'underhang_axial': 'vibration_underhang',
    'underhang_radial': 'vibration_underhang',
    'underhang_tangential': 'vibration_underhang',
    'overhang_axial': 'vibration_overhang',
    'overhang_radial': 'vibration_overhang',
    'overhang_tangential': 'vibration_overhang',
    'microphone': 'acoustic',
}

STAT_CATEGORY = {
    'max': 'peak_magnitude',
    'min': 'peak_magnitude',
    'mean': 'baseline_level',
    'sd': 'general_roughness',
    'rms': 'energy_level',
    'skewness': 'asymmetry',
    'kurtosis': 'impact_signature',
    'crest': 'impact_signature',
    'form': 'waveform_shape',
}

STAT_MEANING = {
    'max': "Peak signal value",
    'min': "Lowest signal value",
    'mean': "Average signal level",
    'sd': "Signal spread/roughness",
    'rms': "Overall vibration energy",
    'skewness': "Signal asymmetry",
    'kurtosis': "Impulsiveness — sharp, repeated impacts",
    'crest': "Peak-to-energy ratio — impact sharpness",
    'form': "Waveform shape descriptor",
}


def categorize_feature(feature_name):
    for channel in sorted(CHANNEL_CATEGORY.keys(), key=len, reverse=True):
        if feature_name.startswith(channel + '_'):
            stat = feature_name[len(channel) + 1:]
            return CHANNEL_CATEGORY[channel], STAT_CATEGORY.get(stat, 'other')
    return 'unknown', 'unknown'


def describe_feature(feature_name):
    for channel in sorted(CHANNEL_CATEGORY.keys(), key=len, reverse=True):
        if feature_name.startswith(channel + '_'):
            stat = feature_name[len(channel) + 1:]
            return f"{STAT_MEANING.get(stat, stat)} — sensor: {channel}"
    return feature_name