import csv
import io
from datetime import datetime, timezone
from typing import Iterable

from fpdf import FPDF


def attendance_to_csv(records: Iterable[dict]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=["user_email", "check_in", "check_out", "status", "location", "notes"],
    )
    writer.writeheader()
    for row in records:
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8")


def attendance_to_pdf(records: Iterable[dict], title: str = "Attendance Report") -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, title, ln=1)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, f"Generado: {datetime.now(timezone.utc).isoformat()} UTC", ln=1)

    pdf.set_font("Arial", "B", 10)
    headers = ["Email", "Check-in", "Check-out", "Status", "Location", "Notes"]
    col_widths = [35, 35, 35, 20, 30, 35]
    for width, header in zip(col_widths, headers):
        pdf.cell(width, 8, header, border=1)
    pdf.ln()

    pdf.set_font("Arial", size=9)
    for row in records:
        values = [
            row.get("user_email", ""),
            row.get("check_in", ""),
            row.get("check_out", ""),
            row.get("status", ""),
            row.get("location", ""),
            row.get("notes", ""),
        ]
        for width, value in zip(col_widths, values):
            pdf.cell(width, 7, str(value)[:50], border=1)
        pdf.ln()
    return pdf.output(dest="S").encode("latin-1")

