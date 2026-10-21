"""
Step 5 — Root Cause Analysis.
Converts the identified phenomenon into a ranked list of probable root causes.
"""

from apps.knowledge.fault_knowledge import PHENOMENON_ROOT_CAUSES


def get_root_causes(phenomenon_id):
    return PHENOMENON_ROOT_CAUSES.get(
        phenomenon_id,
        [{"cause": "Unknown — manual review recommended", "likelihood": "unknown"}]
    )