"""
Step 6 — Maintenance Decision Support.
Converts root causes into actionable maintenance recommendations.
"""

MAINTENANCE_ACTIONS = {
    "Cracked or chipped bearing race/ball": (
        "Perform a visual and borescope inspection of the bearing race and rolling elements. "
        "If damage is confirmed, replace the bearing — continued operation risks rapid "
        "degradation and secondary damage to the shaft or housing."
    ),
    "Debris contamination causing impacts": (
        "Inspect and clean the bearing housing, check seal integrity, and identify the "
        "contamination source (e.g. failed seal, upstream process debris). Replace seals "
        "if compromised."
    ),
    "Early-stage localized surface damage": (
        "Increase monitoring frequency on this machine and schedule a detailed inspection "
        "within the next maintenance window. No immediate replacement needed, but track the "
        "trend closely."
    ),
    "Insufficient lubrication": (
        "Check current lubricant level and condition, replenish or replace as needed, and "
        "verify the lubrication schedule matches manufacturer specification for this bearing."
    ),
    "General bearing wear (no localized damage)": (
        "Monitor the wear trend over successive readings and plan a bearing replacement at "
        "the next scheduled maintenance window, before wear progresses to failure."
    ),
    "Excessive internal clearance or mounting looseness": (
        "Inspect bearing seating and housing fit, and check that all mounting bolts and "
        "fasteners are torqued to specification. Re-secure or shim as needed."
    ),
    "Worn housing fit allowing bearing movement": (
        "Inspect the housing bore for oversize wear. If out of tolerance, consider sleeving "
        "the housing or replacing the housing/bearing assembly."
    ),
    "Uneven load distribution across bearing": (
        "Check shaft loading and alignment, and inspect the bearing for an asymmetric wear "
        "pattern that would confirm uneven loading."
    ),
    "Shaft deflection causing asymmetric wear": (
        "Inspect shaft straightness and the adequacy of its support structure. Correct "
        "excessive overhang or add support if the shaft is deflecting under normal load."
    ),
    "Uneven rotor mass distribution": (
        "Perform a dynamic balancing test to measure vibration amplitude and phase, and "
        "pinpoint the exact location of the imbalance on the rotor."
    ),
    "Missing or shifted balance weights": (
        "Visually inspect balance weight locations, confirm each weight is present and "
        "securely fixed, and reposition or replace any that are missing or shifted."
    ),
    "Coupling misalignment beyond tolerance": (
        "Realign the shaft coupling to specification using a dial indicator or laser "
        "alignment tool, checking both angular and parallel offset."
    ),
    "No fault detected": (
        "No action needed. Continue routine monitoring at the standard interval."
    ),
    "Undetermined — manual review recommended": (
        "Escalate to manual inspection by a qualified technician — the observed pattern is "
        "not recognized by the current automated rule set."
    ),
}


def recommend_actions(root_causes):
    return root_causes