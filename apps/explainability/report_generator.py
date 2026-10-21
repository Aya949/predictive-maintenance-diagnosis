"""
Formats the structured diagnostic result into a human-readable report.
The content is deterministic and comes directly from the diagnostic engine
and knowledge base.
"""


def generate_report(diagnosis: dict) -> str:
    """
    diagnosis: the dict returned by DiagnosticEngine.diagnose()

    Returns:
        A structured diagnostic report containing:
        - predicted condition
        - confidence
        - key contributing factors
        - diagnosed phenomenon
        - probable root causes
        - recommended actions
    """

    lines = []

    lines.append("=" * 60)
    lines.append("MACHINE DIAGNOSTIC REPORT")
    lines.append("=" * 60)

    # ---------------------------------------------------------
    # Diagnosis
    # ---------------------------------------------------------

    lines.append("\n--- Diagnosis ---")
    lines.append(
        f"Predicted condition: {diagnosis['predicted_class']}"
    )
    lines.append(
        f"Confidence: {diagnosis['confidence']:.1%}"
    )

    # ---------------------------------------------------------
    # Key contributing factors
    # ---------------------------------------------------------

    lines.append("\n--- Key Contributing Factors ---")

    for feature in diagnosis["top_features"]:
        lines.append(
            f"• {feature['feature']}"
        )
        lines.append(
            f"  Meaning: {feature['meaning']}"
        )
        lines.append(
            f"  Direction: {feature['direction']}"
        )
        lines.append(
            f"  SHAP contribution: {feature['shap_value']:+.3f}"
        )

    # ---------------------------------------------------------
    # Diagnosed phenomenon
    # ---------------------------------------------------------

    phenomenon = diagnosis.get("phenomenon")

    if phenomenon:
        phenomenon_id = phenomenon.get(
            "phenomenon_id",
            "unknown"
        )

        lines.append("\n--- Diagnosed Phenomenon ---")
        lines.append(
            phenomenon_id.replace("_", " ").title()
        )

    # ---------------------------------------------------------
    # Root causes
    # ---------------------------------------------------------

    lines.append("\n--- Probable Root Cause(s) ---")

    for root_cause in diagnosis["root_causes"]:

        lines.append(
            f"• {root_cause['cause']}"
        )

        lines.append(
            f"  Likelihood: {root_cause['likelihood']}"
        )

        lines.append(
            f"  Explanation: {root_cause['explanation']}"
        )

        lines.append(
            f"  Recommended action: "
            f"{root_cause['recommended_action']}"
        )

    lines.append("\n" + "=" * 60)

    return "\n".join(lines)