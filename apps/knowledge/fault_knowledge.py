"""
Knowledge base: physical phenomenon -> root cause explanation + likelihood.

Each root cause now includes:
- cause: short name (used as the lookup key in maintenance.py — DO NOT rename existing keys)
- likelihood: high / medium / low / unknown
- explanation: plain-language physical explanation for a technician (why this happens,
  what it looks like mechanically)
"""

"""
Knowledge base: physical phenomenon -> root cause explanation + likelihood,
including symptoms, urgency, and an inspection checklist per cause.
"""

PHENOMENON_ROOT_CAUSES = {

    "impact_damage_confirmed": [
        {
            "cause": "Cracked or chipped bearing race/ball",
            "likelihood": "high",
            "explanation": "Vibration and acoustic signals both show an impulsive, impact-like pattern (high kurtosis/crest factor). This is consistent with physical surface damage — a cracked or chipped bearing race or ball element striking the surrounding surface with each rotation.",
            "typical_symptoms": "Sharp, repeated impact spikes in vibration, audible clicking or knocking noise, localized heat at the bearing housing, symptom intensity often tied to rotation frequency.",
            "urgency": "High — localized surface damage typically progresses and can lead to sudden failure if not addressed promptly.",
            "inspection_checklist": [
                "Visually inspect the bearing race and ball elements for cracks or chips",
                "Check for metal debris in the lubricant",
                "Listen for audible knocking or clicking at the bearing housing",
                "Measure vibration amplitude trend over recent readings"
            ],
            "recommended_action": "Inspect bearing surface visually for damage; replace the bearing if cracking or chipping is confirmed.",
        },
        {
            "cause": "Debris contamination causing impacts",
            "likelihood": "medium",
            "explanation": "Foreign particles (metal shavings, dust, or contaminants) trapped inside the bearing can strike internal surfaces during rotation, producing an impulsive vibration and acoustic signature similar to physical bearing damage.",
            "typical_symptoms": "Irregular, non-periodic impact spikes, gritty or crunching sound, possible discoloration of the lubricant.",
            "urgency": "Medium to high — depends on the amount and hardness of contaminant; can accelerate wear rapidly.",
            "inspection_checklist": [
                "Inspect and clean the bearing housing",
                "Check seal integrity to identify how contaminants entered",
                "Inspect lubricant for visible particles or discoloration",
                "Verify the surrounding environment for dust/debris sources"
            ],
            "recommended_action": "Inspect and clean the bearing housing; check seal integrity to prevent further contamination.",
        },
    ],

    "impact_damage_early": [
        {
            "cause": "Early-stage localized surface damage",
            "likelihood": "medium",
            "explanation": "Vibration shows an impulsive pattern (elevated kurtosis/crest factor) without a strong accompanying acoustic signature, suggesting a small, localized defect that has not yet developed into major surface damage.",
            "typical_symptoms": "Intermittent or low-amplitude impact spikes in vibration, no audible abnormal noise yet, no significant temperature rise.",
            "urgency": "Moderate — early stage, but worth tracking closely since localized defects tend to worsen over time.",
            "inspection_checklist": [
                "Schedule a follow-up vibration reading to confirm trend",
                "Perform a visual inspection at the next accessible maintenance window",
                "Monitor kurtosis/crest factor trend over successive readings"
            ],
            "recommended_action": "Schedule closer monitoring; plan a physical inspection within the next maintenance window.",
        },
    ],

    "wear_or_lubrication": [
        {
            "cause": "Insufficient lubrication",
            "likelihood": "high",
            "explanation": "Without an adequate lubricant film, metal surfaces inside the bearing make more direct contact, increasing friction and overall vibration energy across a broad frequency range rather than at sharp, distinct impact peaks.",
            "typical_symptoms": "Gradually rising vibration energy (RMS) over time, elevated operating temperature, audible friction noise, no sharp impact signature.",
            "urgency": "Moderate — degrades progressively, but can accelerate wear on other components if left unaddressed.",
            "inspection_checklist": [
                "Check current lubricant level and condition",
                "Verify lubrication schedule matches manufacturer specification",
                "Inspect for lubricant contamination or degradation",
                "Check seal integrity to rule out leakage"
            ],
            "recommended_action": "Check current lubricant level and condition, replenish or replace as needed, and verify the lubrication schedule matches manufacturer specification for this bearing.",
        },
        {
            "cause": "General bearing wear (no localized damage)",
            "likelihood": "medium",
            "explanation": "Cumulative, evenly distributed wear across the bearing surfaces increases internal roughness and vibration energy over time, without a single identifiable defect point. This is typical of a bearing nearing the end of its normal service life.",
            "typical_symptoms": "Slow, steady increase in vibration energy over successive readings, no sharp localized spikes, gradual rather than sudden onset.",
            "urgency": "Low to moderate — expected end-of-life behavior; plan replacement rather than emergency response.",
            "inspection_checklist": [
                "Review bearing service hours against expected lifespan",
                "Monitor vibration RMS trend over successive readings",
                "Plan replacement at the next scheduled maintenance window"
            ],
            "recommended_action": "Monitor the wear trend over successive readings and plan a bearing replacement at the next scheduled maintenance window, before wear progresses to failure.",
        },
    ],

    "clearance_or_looseness": [
        {
            "cause": "Excessive internal clearance or mounting looseness",
            "likelihood": "high",
            "explanation": "Elevated peak vibration amplitudes without an accompanying impact-type waveform shape suggest components are moving more freely than intended, producing larger amplitude swings rather than sharp, localized impacts.",
            "typical_symptoms": "Elevated peak (max/min) vibration values, inconsistent readings between cycles, possible audible rattling.",
            "urgency": "Moderate to high — loose components can accelerate wear on adjacent parts if not corrected.",
            "inspection_checklist": [
                "Inspect bearing seating and housing fit",
                "Check mounting bolts and fasteners for looseness",
                "Verify shaft and bearing clearance against specification"
            ],
            "recommended_action": "Inspect bearing seating and housing fit; check mounting bolts/fasteners for looseness.",
        },
        {
            "cause": "Worn housing fit allowing bearing movement",
            "likelihood": "medium",
            "explanation": "Over time, the housing bore can wear larger than its original tolerance, allowing the bearing outer race to shift slightly during operation, producing elevated and inconsistent vibration amplitudes.",
            "typical_symptoms": "Amplitude variability across readings, no consistent impact frequency, potential slight axial or radial play detectable by hand when accessible.",
            "urgency": "Moderate — progressive wear that will worsen if unaddressed.",
            "inspection_checklist": [
                "Inspect housing bore for wear or oversize condition",
                "Check for detectable play in the bearing when accessible",
                "Consider housing or bearing replacement if wear is confirmed"
            ],
            "recommended_action": "Inspect housing bore for wear; consider bearing/housing replacement if excessive play is confirmed.",
        },
    ],

    "uneven_load_wear": [
        {
            "cause": "Uneven load distribution across bearing",
            "likelihood": "high",
            "explanation": "Waveform shape and asymmetry features suggest the bearing is experiencing non-uniform loading, causing certain sections of the bearing to wear faster than others rather than a single localized defect.",
            "typical_symptoms": "Asymmetric vibration waveform, uneven wear pattern if visually inspected, possible correlation with load or operating condition changes.",
            "urgency": "Moderate — can accelerate localized wear if the underlying load imbalance is not corrected.",
            "inspection_checklist": [
                "Check shaft loading and alignment",
                "Inspect for uneven wear pattern on the bearing surface",
                "Review recent changes in operating load or conditions"
            ],
            "recommended_action": "Check shaft loading and alignment; inspect for uneven wear pattern.",
        },
        {
            "cause": "Shaft deflection causing asymmetric wear",
            "likelihood": "medium",
            "explanation": "A bent or deflected shaft can cause the bearing to experience cyclically uneven loading with each rotation, producing an asymmetric vibration waveform distinct from a centered, evenly-loaded bearing.",
            "typical_symptoms": "Asymmetric waveform correlated with rotation frequency, potential visible shaft runout if measured.",
            "urgency": "Moderate to high — shaft deflection can affect multiple downstream components if uncorrected.",
            "inspection_checklist": [
                "Inspect shaft straightness and support structure",
                "Measure shaft runout if equipment is accessible",
                "Check for signs of deflection under load"
            ],
            "recommended_action": "Inspect shaft straightness and support structure.",
        },
    ],

    "mass_imbalance": [
        {
            "cause": "Uneven rotor mass distribution",
            "likelihood": "high",
            "explanation": "The rotor's mass is not evenly distributed around its rotation axis, so the centrifugal force pulls harder on one side with every revolution. This produces a periodic vibration at the rotation frequency, similar to an unbalanced washing machine drum. Common causes include material buildup (dust, corrosion) on one side, uneven wear, or a manufacturing/installation defect.",
            "typical_symptoms": "Periodic vibration synchronized with rotation speed, smooth (non-impulsive) waveform, amplitude proportional to rotation speed.",
            "urgency": "Moderate — steady-state issue that can accelerate bearing wear over time if uncorrected.",
            "inspection_checklist": [
                "Perform a dynamic balancing test to measure vibration amplitude and phase",
                "Pinpoint the exact location of imbalance on the rotor",
                "Check for material buildup, corrosion, or debris on the rotor"
            ],
            "recommended_action": "Perform a dynamic balancing test to measure vibration amplitude and phase, and pinpoint the exact location of the imbalance on the rotor.",
        },
        {
            "cause": "Missing or shifted balance weights",
            "likelihood": "medium",
            "explanation": "Rotors are normally fitted with small correction weights during manufacturing or maintenance to offset natural mass irregularities. If these weights have come loose, fallen off, or shifted position over time, the rotor reverts to its original unbalanced state.",
            "typical_symptoms": "Sudden onset of imbalance-type vibration (if weights recently shifted), periodic vibration at rotation frequency.",
            "urgency": "Moderate — straightforward to correct once identified, but should not be left unaddressed.",
            "inspection_checklist": [
                "Visually inspect balance weight locations",
                "Confirm each weight is present and securely fixed",
                "Reposition or replace any weights that are missing or shifted"
            ],
            "recommended_action": "Visually inspect balance weight locations, confirm each weight is present and securely fixed, and reposition or replace any that are missing or shifted.",
        },
    ],

    "shaft_misalignment": [
        {
            "cause": "Coupling misalignment beyond tolerance",
            "likelihood": "high",
            "explanation": "The shaft coupling between the motor and driven equipment is offset beyond acceptable tolerance, either angularly or parallel. This produces abnormal vibration patterns concentrated in the plane of misalignment, along with additional stress on bearings and seals.",
            "typical_symptoms": "Vibration concentrated at rotation frequency and its harmonics, direction-dependent amplitude (horizontal vs vertical), potential coupling or seal wear.",
            "urgency": "Moderate to high — uncorrected misalignment accelerates wear on bearings, seals, and the coupling itself.",
            "inspection_checklist": [
                "Check shaft coupling alignment against tolerance specification",
                "Inspect coupling components for visible wear",
                "Verify mounting base has not shifted or settled"
            ],
            "recommended_action": "Realign shaft coupling per specification.",
        },
    ],

    "healthy_operation": [
        {
            "cause": "No fault detected",
            "likelihood": "high",
            "explanation": "All monitored signals fall within expected baseline ranges, with no impact, elevated energy, or asymmetry signatures detected — consistent with normal operating condition.",
            "typical_symptoms": "Stable vibration levels within normal range, no impact or asymmetry signatures, consistent readings over time.",
            "urgency": "None — routine monitoring is sufficient.",
            "inspection_checklist": [
                "Continue routine monitoring schedule",
                "No immediate action required"
            ],
            "recommended_action": "No action needed. Continue routine monitoring.",
        },
    ],

    "unmatched_pattern": [
        {
            "cause": "Undetermined — manual review recommended",
            "likelihood": "unknown",
            "explanation": "The combination of contributing features did not match any of the currently defined diagnostic patterns. This does not necessarily indicate a problem, but the pattern falls outside the system's current rule coverage.",
            "typical_symptoms": "N/A — pattern not yet characterized.",
            "urgency": "Unknown — requires manual review to determine appropriate response.",
            "inspection_checklist": [
                "Manually review the top contributing features for this reading",
                "Compare against recent readings for the same machine",
                "Consider this case for future rule refinement"
            ],
            "recommended_action": "Escalate to manual inspection; pattern not recognized by current rules.",
        },
    ],

}