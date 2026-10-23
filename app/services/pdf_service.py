from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def build_payslip_pdf(entry, company_name, company_address):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=14*mm, bottomMargin=14*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=8, leading=11))
    employee = entry.employee
    period = entry.period

    story = [
        Paragraph(company_name, styles["Title"]),
        Paragraph(company_address, styles["Small"]),
        Spacer(1, 8),
        Paragraph(f"Salary Slip — {period.label}", styles["Heading2"]),
        Spacer(1, 8),
    ]
    info = [
        ["Employee", employee.display_name, "Employee ID", employee.employee_code],
        ["Department", employee.department.name, "Designation", employee.designation],
        ["Bank", employee.bank_name or "—", "Account", employee.bank_account or "—"],
        ["PAN", employee.pan_number or "—", "UAN", employee.uan_number or "—"],
        ["Attendance", f"{entry.attendance_days} days", "Paid leave", f"{entry.paid_leave_days} days"],
    ]
    info_table = Table(info, colWidths=[30*mm, 55*mm, 30*mm, 55*mm])
    info_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.35, colors.grey),
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#edf2f7")),
        ("BACKGROUND", (2,0), (2,-1), colors.HexColor("#edf2f7")),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (2,0), (2,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("PADDING", (0,0), (-1,-1), 6),
    ]))
    story.extend([info_table, Spacer(1, 12)])

    earnings = [["Earnings", "Amount (INR)"]]
    deductions = [["Deductions", "Amount (INR)"]]
    for item in entry.line_items:
        row = [item.description, f"{float(item.amount):,.2f}"]
        (earnings if item.category == "earning" else deductions).append(row)
    earnings.append(["Gross Pay", f"{float(entry.gross_pay):,.2f}"])
    deductions.append(["Total Deductions", f"{float(entry.total_deductions):,.2f}"])
    max_rows = max(len(earnings), len(deductions))
    earnings += [["", ""]] * (max_rows - len(earnings))
    deductions += [["", ""]] * (max_rows - len(deductions))
    combined = [[*earnings[i], *deductions[i]] for i in range(max_rows)]
    pay_table = Table(combined, colWidths=[55*mm, 30*mm, 55*mm, 30*mm])
    pay_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.35, colors.grey),
        ("BACKGROUND", (0,0), (1,0), colors.HexColor("#dff4e4")),
        ("BACKGROUND", (2,0), (3,0), colors.HexColor("#fde7e7")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
        ("ALIGN", (1,0), (1,-1), "RIGHT"),
        ("ALIGN", (3,0), (3,-1), "RIGHT"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("PADDING", (0,0), (-1,-1), 6),
    ]))
    story.extend([pay_table, Spacer(1, 12)])
    net_table = Table([["NET PAY", f"INR {float(entry.net_pay):,.2f}"]], colWidths=[110*mm, 60*mm])
    net_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#193b68")),
        ("TEXTCOLOR", (0,0), (-1,-1), colors.white),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 13),
        ("ALIGN", (1,0), (1,0), "RIGHT"),
        ("PADDING", (0,0), (-1,-1), 9),
    ]))
    story.extend([net_table, Spacer(1, 14), Paragraph("This is a system-generated salary slip and does not require a signature.", styles["Small"])])
    doc.build(story)
    buffer.seek(0)
    return buffer
