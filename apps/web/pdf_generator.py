"""
Professional PDF diagnostic report generator.

Visual language matches the JESA Maintenance Intelligence web platform:
light background, JESA-inspired blue palette, clean engineering layout.

The PDF is generated entirely in memory and can be:
- downloaded by the user
- attached to an email
- returned directly by the FastAPI endpoint
"""

from io import BytesIO
from html import escape

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)


# ============================================================
# JESA PLATFORM COLORS
# ============================================================

PRIMARY = HexColor("#0756A5")
PRIMARY_DARK = HexColor("#043D78")
PRIMARY_LIGHT = HexColor("#EAF3FF")

ACCENT = HexColor("#18A0AE")

SUCCESS = HexColor("#159570")
SUCCESS_BG = HexColor("#EAF8F3")

WARNING = HexColor("#D98B16")
WARNING_BG = HexColor("#FFF6E5")

DANGER = HexColor("#D94B52")
DANGER_BG = HexColor("#FFF0F1")

TEXT = HexColor("#17263A")
TEXT_SECONDARY = HexColor("#53657A")
TEXT_MUTED = HexColor("#8492A3")

BORDER = HexColor("#E4EAF1")
BACKGROUND = HexColor("#F5F7FA")
WHITE = colors.white


# ============================================================
# HELPERS
# ============================================================

def _safe(value, default=""):
    """Convert values safely to ReportLab-friendly text."""
    if value is None:
        return default

    return escape(str(value))


def _confidence_label(confidence):
    """Return confidence label and matching colors."""

    if confidence >= 0.90:
        return "HIGH CONFIDENCE", SUCCESS, SUCCESS_BG

    if confidence >= 0.70:
        return "MODERATE CONFIDENCE", WARNING, WARNING_BG

    return "LOW CONFIDENCE", DANGER, DANGER_BG


def _is_normal(predicted_class):
    return str(predicted_class).strip().lower() == "normal"


def _split_narrative(narrative):
    """
    Normalize the optional LLM narrative.

    Returns an empty list if the LLM is unavailable.
    """

    if not narrative:
        return []

    cleaned = str(narrative).strip()

    # Remove headings if the LLM returned them.
    cleaned = cleaned.replace(
        "Diagnostic Summary",
        "",
    )

    cleaned = cleaned.replace(
        "Engineering Details",
        "",
    )

    paragraphs = [
        paragraph.strip()
        for paragraph in cleaned.split("\n\n")
        if paragraph.strip()
    ]

    return paragraphs


# ============================================================
# HEADER / FOOTER
# ============================================================

def _draw_page_header_footer(canvas, doc):
    """Draw the consistent report header and footer."""

    canvas.saveState()

    width, height = A4

    # --------------------------------------------------------
    # Header line
    # --------------------------------------------------------

    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.6)

    canvas.line(
        18 * mm,
        height - 16 * mm,
        width - 18 * mm,
        height - 16 * mm,
    )

    # --------------------------------------------------------
    # JESA mark
    # --------------------------------------------------------

    canvas.setFillColor(PRIMARY)

    canvas.roundRect(
        18 * mm,
        height - 12.8 * mm,
        9 * mm,
        7 * mm,
        1.8 * mm,
        fill=1,
        stroke=0,
    )

    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 9)

    canvas.drawCentredString(
        22.5 * mm,
        height - 10.7 * mm,
        "J",
    )

    canvas.setFillColor(TEXT)
    canvas.setFont("Helvetica-Bold", 8.5)

    canvas.drawString(
        30 * mm,
        height - 10.5 * mm,
        "JESA Maintenance Intelligence",
    )

    # --------------------------------------------------------
    # Footer
    # --------------------------------------------------------

    canvas.setStrokeColor(BORDER)

    canvas.line(
        18 * mm,
        14 * mm,
        width - 18 * mm,
        14 * mm,
    )

    canvas.setFillColor(TEXT_MUTED)
    canvas.setFont("Helvetica", 7.5)

    canvas.drawString(
        18 * mm,
        8.5 * mm,
        "Engineering diagnostic decision-support report",
    )

    canvas.drawRightString(
        width - 18 * mm,
        8.5 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


# ============================================================
# MAIN PDF GENERATOR
# ============================================================


def generate_pdf_report(reading, prediction, machine, root_causes=None, narrative=None) -> BytesIO:
    root_causes = root_causes or []
    
    machine_code = machine.machine_code
    machine_name = machine.name
    meta = {"machine_id": machine.machine_code, "reading_id": reading.id}


    # IMPORTANT:
    # Always initialize this even if the LLM is unavailable.
    narrative_paragraphs = _split_narrative(narrative)

    # ========================================================
    # DOCUMENT
    # ========================================================

    buffer = BytesIO()

    doc = BaseDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=24 * mm,
        bottomMargin=21 * mm,
        title="Maintenance Diagnostic Report",
        author="JESA Maintenance Intelligence",
    )

    frame = Frame(
        18 * mm,
        21 * mm,
        A4[0] - 36 * mm,
        A4[1] - 45 * mm,
        id="main",
    )

    doc.addPageTemplates(
        [
            PageTemplate(
                id="report",
                frames=[frame],
                onPage=_draw_page_header_footer,
            )
        ]
    )

    # ========================================================
    # STYLES
    # ========================================================

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=21,
        leading=24,
        textColor=TEXT,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=TEXT_MUTED,
    )

    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12,
        textColor=PRIMARY,
        spaceBefore=13,
        spaceAfter=7,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=14,
        textColor=TEXT_SECONDARY,
        spaceAfter=5,
    )

    small_style = ParagraphStyle(
        "Small",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=TEXT_MUTED,
    )

    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=9,
        textColor=TEXT_MUTED,
    )

    value_style = ParagraphStyle(
        "Value",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        textColor=TEXT,
    )

    cause_title_style = ParagraphStyle(
        "CauseTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=TEXT,
        spaceAfter=2,
    )

    cause_body_style = ParagraphStyle(
        "CauseBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8.8,
        leading=14,
        textColor=TEXT_SECONDARY,
    )

    action_style = ParagraphStyle(
        "Action",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12,
        textColor=PRIMARY_DARK,
    )

    # ========================================================
    # CONTENT
    # ========================================================

    elements = []

    predicted_class = str(
        getattr(
            prediction,
            "predicted_class",
            "",
        )
    )

    confidence = float(
        getattr(
            prediction,
            "confidence",
            0,
        )
    )

    machine_id = machine.machine_code

    reading_id = getattr(
        reading,
        "id",
        "—",
    )

    created_at = getattr(
        prediction,
        "created_at",
        None,
    )

    file_source = getattr(
        reading,
        "source",
        "Unknown",
    )

    confidence_label, confidence_color, confidence_bg = (
        _confidence_label(confidence)
    )

    normal = _is_normal(predicted_class)

    # ========================================================
    # TITLE
    # ========================================================

    elements.append(
        Spacer(1, 2 * mm)
    )

    elements.append(
        Paragraph(
            "MAINTENANCE DIAGNOSTIC REPORT",
            title_style,
        )
    )

    elements.append(
        Paragraph(
            "Engineering Diagnostic Reasoning Engine",
            subtitle_style,
        )
    )

    elements.append(
        Spacer(1, 6 * mm)
    )

    # ========================================================
    # MACHINE META
    # ========================================================

    machine_info = Table(
        [
            [
                Paragraph("MACHINE", label_style),
                Paragraph("READING", label_style),
                Paragraph("DATE", label_style),
                Paragraph("SOURCE", label_style),
            ],
            [
                Paragraph(
                    _safe(machine_id),
                    value_style,
                ),
                Paragraph(
                    f"#{_safe(reading_id)}",
                    value_style,
                ),
                Paragraph(
                    _safe(
                        created_at.strftime(
                            "%d %b %Y · %H:%M"
                        )
                        if created_at
                        else "—"
                    ),
                    value_style,
                ),
                Paragraph(
                    _safe(file_source),
                    value_style,
                ),
            ],
        ],
        colWidths=[
            43 * mm,
            31 * mm,
            56 * mm,
            46 * mm,
        ],
    )

    machine_info.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    WHITE,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    BORDER,
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    BORDER,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    elements.append(machine_info)

    elements.append(
        Spacer(1, 5 * mm)
    )

    # ========================================================
    # DIAGNOSIS HERO
    # ========================================================

    hero_label = ParagraphStyle(
        "HeroLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        textColor=HexColor("#BFD9F4"),
    )

    hero_title = ParagraphStyle(
        "HeroTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=21,
        textColor=WHITE,
    )

    hero_description = ParagraphStyle(
        "HeroDescription",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=HexColor("#DCEBFA"),
    )

    hero_confidence = ParagraphStyle(
        "HeroConfidence",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=21,
        textColor=WHITE,
        alignment=2,
    )

    hero_status = ParagraphStyle(
        "HeroStatus",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        textColor=WHITE,
        alignment=2,
    )

    hero_left = [
        Paragraph(
            "DETECTED CONDITION",
            hero_label,
        ),
        Spacer(1, 1.5 * mm),
        Paragraph(
            _safe(
                predicted_class.replace(
                    "_",
                    " ",
                ).title()
            ),
            hero_title,
        ),
        Spacer(1, 1.5 * mm),
        Paragraph(
            (
                "No abnormal condition identified."
                if normal
                else
                "Condition requires engineering attention."
            ),
            hero_description,
        ),
    ]

    hero_right = [
        Paragraph(
            "MODEL CONFIDENCE",
            hero_label,
        ),
        Spacer(1, 1.5 * mm),
        Paragraph(
            f"{confidence:.1%}",
            hero_confidence,
        ),
        Spacer(1, 1.5 * mm),
        Paragraph(
            confidence_label,
            hero_status,
        ),
    ]

    hero_table = Table(
        [
            [
                hero_left,
                hero_right,
            ]
        ],
        colWidths=[
            120 * mm,
            57 * mm,
        ],
    )

    hero_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    PRIMARY,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (0, 0),
                    11,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (0, 0),
                    8,
                ),
                (
                    "LEFTPADDING",
                    (1, 0),
                    (1, 0),
                    8,
                ),
                (
                    "RIGHTPADDING",
                    (1, 0),
                    (1, 0),
                    11,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
            ]
        )
    )

    elements.append(hero_table)

    # ========================================================
    # DIAGNOSTIC SUMMARY
    # ========================================================

    if narrative_paragraphs:

        elements.append(
            Paragraph(
                "DIAGNOSTIC SUMMARY",
                section_style,
            )
        )

        elements.append(
            Paragraph(
                _safe(
                    narrative_paragraphs[0]
                ),
                body_style,
            )
        )

    # ========================================================
    # KEY CONTRIBUTING SIGNALS
    # ========================================================

    elements.append(
        Paragraph(
            "KEY CONTRIBUTING SIGNALS",
            section_style,
        )
    )

    top_features = (
        getattr(
            prediction,
            "top_features",
            None,
        )
        or []
    )

    if top_features:

        feature_data = [
            [
                Paragraph(
                    "FEATURE",
                    label_style,
                ),
                Paragraph(
                    "PHYSICAL MEANING",
                    label_style,
                ),
                Paragraph(
                    "IMPACT",
                    label_style,
                ),
            ]
        ]

        for feature in top_features[:6]:

            feature_name = feature.get(
                "feature",
                "",
            )

            meaning = feature.get(
                "meaning",
                "",
            )

            shap_value = float(
                feature.get(
                    "shap_value",
                    0,
                )
            )

            direction = feature.get(
                "direction",
                "",
            )

            impact_style = ParagraphStyle(
                "ImpactCell",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=8,
                leading=10,
                textColor=(
                    DANGER
                    if shap_value > 0
                    else PRIMARY
                ),
            )

            feature_data.append(
                [
                    Paragraph(
                        _safe(feature_name),
                        ParagraphStyle(
                            "FeatureName",
                            parent=styles["Normal"],
                            fontName="Helvetica-Bold",
                            fontSize=8,
                            leading=10,
                            textColor=TEXT,
                        ),
                    ),
                    Paragraph(
                        _safe(meaning),
                        small_style,
                    ),
                    Paragraph(
                        f"{shap_value:+.3f}<br/>"
                        f"<font size='6.5'>"
                        f"{_safe(direction)}"
                        f"</font>",
                        impact_style,
                    ),
                ]
            )

        feature_table = Table(
            feature_data,
            colWidths=[
                48 * mm,
                96 * mm,
                33 * mm,
            ],
            repeatRows=1,
        )

        feature_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        PRIMARY_LIGHT,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        BORDER,
                    ),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [WHITE, BACKGROUND],
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        elements.append(feature_table)

    else:

        elements.append(
            Paragraph(
                "No feature contribution analysis is available "
                "for this reading.",
                body_style,
            )
        )

    # ========================================================
    # ENGINEERING INTERPRETATION
    # ========================================================

    if len(narrative_paragraphs) > 1:

        elements.append(
            Paragraph(
                "ENGINEERING INTERPRETATION",
                section_style,
            )
        )

        elements.append(
            Paragraph(
                _safe(
                    narrative_paragraphs[1]
                ),
                body_style,
            )
        )

    # ========================================================
    # PROBABLE ROOT CAUSES
    # ========================================================

    elements.append(
        Paragraph(
            "PROBABLE ROOT CAUSES",
            section_style,
        )
    )

    if root_causes:

        for index, rc in enumerate(
            root_causes,
            start=1,
        ):

            cause = rc.get(
                "cause",
                "Unknown cause",
            )

            likelihood = str(
                rc.get(
                    "likelihood",
                    "unknown",
                )
            )

            explanation = rc.get(
                "explanation",
                "",
            )

            typical_symptoms = rc.get(
                "typical_symptoms",
                "",
            )

            urgency = rc.get(
                "urgency",
                "",
            )

            recommended_action = rc.get(
                "recommended_action",
                "",
            )

            # Cause title
            elements.append(
                KeepTogether(
                    [
                        Paragraph(
                            f"{index:02d}  "
                            f"{_safe(cause)}",
                            cause_title_style,
                        ),
                        Paragraph(
                            f"<b>Likelihood:</b> "
                            f"{_safe(likelihood).capitalize()}",
                            small_style,
                        ),
                    ]
                )
            )

            # Explanation
            if explanation:

                elements.append(
                    Spacer(1, 1.5 * mm)
                )

                elements.append(
                    Paragraph(
                        _safe(explanation),
                        cause_body_style,
                    )
                )

            # Typical symptoms
            if typical_symptoms:

                elements.append(
                    Paragraph(
                        f"<b>Typical indicators:</b> "
                        f"{_safe(typical_symptoms)}",
                        cause_body_style,
                    )
                )

            # Urgency
            if urgency:

                elements.append(
                    Paragraph(
                        f"<b>Priority:</b> "
                        f"{_safe(urgency)}",
                        cause_body_style,
                    )
                )

            # Recommended action
            if recommended_action:

                elements.append(
                    Spacer(1, 1.5 * mm)
                )

                elements.append(
                    Paragraph(
                        f"<b>Recommended action:</b> "
                        f"{_safe(recommended_action)}",
                        action_style,
                    )
                )

            if index < len(root_causes):

                elements.append(
                    Spacer(1, 3 * mm)
                )

                elements.append(
                    HRFlowable(
                        width="100%",
                        thickness=0.35,
                        color=BORDER,
                        spaceBefore=1,
                        spaceAfter=6,
                    )
                )

    else:

        elements.append(
            Paragraph(
                "No probable root cause is available "
                "for this diagnostic result.",
                body_style,
            )
        )

    # ========================================================
    # MAINTENANCE RECOMMENDATION
    # ========================================================

    recommendations = [
        rc.get("recommended_action")
        for rc in root_causes
        if rc.get("recommended_action")
    ]

    if recommendations:

        elements.append(
            Paragraph(
                "MAINTENANCE RECOMMENDATION",
                section_style,
            )
        )

        if len(recommendations) == 1:

            recommendation_text = _safe(
                recommendations[0]
            )

        elif len(recommendations) == 2:

            recommendation_text = (
                f"{_safe(recommendations[0])} "
                f"{_safe(recommendations[1])}"
            )

        else:

            recommendation_text = " ".join(
                _safe(action)
                for action in recommendations
            )

        recommendation_box = Table(
            [
                [
                    Paragraph(
                        recommendation_text,
                        action_style,
                    )
                ]
            ],
            colWidths=[177 * mm],
        )

        recommendation_box.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        PRIMARY_LIGHT,
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.7,
                        HexColor("#BCD5F0"),
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        10,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        10,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        9,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        9,
                    ),
                ]
            )
        )

        elements.append(
            recommendation_box
        )

    # ========================================================
    # DISCLAIMER
    # ========================================================

    elements.append(
        Spacer(1, 8 * mm)
    )

    elements.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=BORDER,
        )
    )

    elements.append(
        Spacer(1, 3 * mm)
    )

    elements.append(
        Paragraph(
            "<b>Decision-support notice:</b> "
            "This report presents an automated engineering assessment "
            "based on available sensor data, model output, and diagnostic "
            "rules. It is intended to support qualified maintenance "
            "personnel and does not replace physical inspection or "
            "engineering judgment.",
            small_style,
        )
    )

    # ========================================================
    # BUILD PDF
    # ========================================================

    doc.build(elements)

    buffer.seek(0)

    return buffer