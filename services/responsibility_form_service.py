import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def safe_value(value):
    if value is None or value == "":
        return "-"

    return str(value)


def generate_responsibility_form(
    output_path,
    form_number,
    generation_date,
    data,
    comments=None,
):
    os.makedirs(
        os.path.dirname(output_path),
        exist_ok=True,
    )

    document = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "ASSET RESPONSIBILITY FORM",
            styles["Title"],
        )
    )

    story.append(
        Spacer(1, 12)
    )

    header_data = [
        [
            "Form Number",
            safe_value(form_number),
        ],
        [
            "Generation Date",
            safe_value(generation_date),
        ],
    ]

    header_table = Table(
        header_data,
        colWidths=[
            50 * mm,
            100 * mm,
        ],
    )

    header_table.setStyle(
        TableStyle([
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey,
            ),
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.whitesmoke,
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
        ])
    )

    story.append(header_table)

    story.append(
        Spacer(1, 18)
    )

    story.append(
        Paragraph(
            "Employee Information",
            styles["Heading2"],
        )
    )

    employee_data = [
        [
            "Employee",
            safe_value(
                data.get("EmployeeName")
            ),
        ],
        [
            "Position",
            safe_value(
                data.get("Position")
            ),
        ],
        [
            "Area",
            safe_value(
                data.get("Area")
            ),
        ],
        [
            "Business Line",
            safe_value(
                data.get("BusinessLine")
            ),
        ],
        [
            "Office",
            safe_value(
                data.get("Office")
            ),
        ],
        [
            "Direct Supervisor",
            safe_value(
                data.get("DirectSupervisor")
            ),
        ],
    ]

    employee_table = Table(
        employee_data,
        colWidths=[
            50 * mm,
            100 * mm,
        ],
    )

    employee_table.setStyle(
        TableStyle([
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey,
            ),
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.whitesmoke,
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
        ])
    )

    story.append(employee_table)

    story.append(
        Spacer(1, 18)
    )

    story.append(
        Paragraph(
            "Equipment Information",
            styles["Heading2"],
        )
    )

    equipment_data = [
        [
            "Code",
            safe_value(
                data.get("Code")
            ),
        ],
        [
            "Type",
            safe_value(
                data.get("Type")
            ),
        ],
        [
            "Brand",
            safe_value(
                data.get("Brand")
            ),
        ],
        [
            "Model",
            safe_value(
                data.get("Model")
            ),
        ],
        [
            "Serial Number",
            safe_value(
                data.get("SerialNumber")
            ),
        ],
        [
            "Charger Serial",
            safe_value(
                data.get("ChargerSerialNumber")
            ),
        ],
        [
            "Fixed Asset",
            safe_value(
                data.get("FixedAsset")
            ),
        ],
        [
            "Assignment Date",
            safe_value(
                data.get("AssignmentDate")
            ),
        ],
    ]

    equipment_table = Table(
        equipment_data,
        colWidths=[
            50 * mm,
            100 * mm,
        ],
    )

    equipment_table.setStyle(
        TableStyle([
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey,
            ),
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.whitesmoke,
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
        ])
    )

    story.append(equipment_table)

    story.append(
        Spacer(1, 20)
    )

    responsibility_text = (
        "Por medio de la presente, el colaborador confirma "
        "la recepción del equipo descrito en este documento "
        "y acepta mantenerlo bajo su resguardo durante el "
        "periodo de asignación."
    )

    story.append(
        Paragraph(
            responsibility_text,
            styles["BodyText"],
        )
    )

    if comments:
        story.append(
            Spacer(1, 12)
        )

        story.append(
            Paragraph(
                "<b>Comments</b>",
                styles["BodyText"],
            )
        )

        story.append(
            Paragraph(
                safe_value(comments),
                styles["BodyText"],
            )
        )

    story.append(
        Spacer(1, 40)
    )

    signatures = Table(
        [
            [
                "____________________________",
                "____________________________",
            ],
            [
                safe_value(
                    data.get("EmployeeName")
                ),
                "IT Support",
            ],
            [
                "Employee Signature",
                "IT Signature",
            ],
        ],
        colWidths=[
            75 * mm,
            75 * mm,
        ],
    )

    signatures.setStyle(
        TableStyle([
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER",
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                9,
            ),
        ])
    )

    story.append(signatures)

    document.build(story)