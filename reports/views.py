import csv
from io import BytesIO
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from dashboard.services import date_bounds, report_data

@login_required
def report_view(request):
    start,end,preset=date_bounds(request); data=report_data(request.user,start,end); data["preset"]=preset
    return render(request,"reports/index.html",data)
@login_required
def export_report(request,format):
    start,end,_=date_bounds(request); data=report_data(request.user,start,end); rows=data["bookings"]
    if format=="csv":
        response=HttpResponse(content_type="text/csv"); response["Content-Disposition"]='attachment; filename="turfiq-report.csv"'; w=csv.writer(response); w.writerow(["Date","Customer","Phone","Sport","Ground","Amount","Payment","Status"])
        for b in rows: w.writerow([b.booking_date,b.customer.name,b.customer.phone,b.sport,b.ground,b.amount,b.payment_method,b.status])
        return response
    if format=="xlsx":
        wb=Workbook(); ws=wb.active; ws.title="Bookings"; ws.append(["Date","Customer","Phone","Sport","Ground","Amount","Payment","Status"])
        for b in rows: ws.append([b.booking_date,b.customer.name,b.customer.phone,b.sport,str(b.ground),float(b.amount),b.payment_method,b.status])
        header_fill = PatternFill("solid", fgColor="128A4B")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_border = Border(bottom=Side(style="medium", color="0B5D32"))
        body_border = Border(bottom=Side(style="thin", color="DDE8E1"))
        alternate_fill = PatternFill("solid", fgColor="F0F8F3")
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.border = header_border
            cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 26
        for row_number in range(2, ws.max_row + 1):
            for cell in ws[row_number]:
                cell.font = Font(name="Calibri", size=11, bold=False, color="24352B")
                cell.border = body_border
                cell.alignment = Alignment(vertical="center")
                if row_number % 2 == 0:
                    cell.fill = alternate_fill
            ws.cell(row_number, 1).number_format = "dd-mmm-yyyy"
            ws.cell(row_number, 6).number_format = '₹#,##0.00'
            ws.cell(row_number, 6).alignment = Alignment(horizontal="right", vertical="center")
            ws.row_dimensions[row_number].height = 21
        column_widths = [14, 24, 17, 18, 22, 16, 18, 16]
        for index, width in enumerate(column_widths, start=1):
            ws.column_dimensions[get_column_letter(index)].width = width
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        ws.sheet_view.showGridLines = False
        ws.print_title_rows = "1:1"
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_view.zoomScale = 90
        output=BytesIO(); wb.save(output); response=HttpResponse(output.getvalue(),content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"); response["Content-Disposition"]='attachment; filename="turfiq-report.xlsx"'; return response
    output=BytesIO(); pdf=canvas.Canvas(output,pagesize=A4); y=800; pdf.setFont("Helvetica-Bold",16); pdf.drawString(40,y,"TurfIQ Analytics Report"); y-=28; pdf.setFont("Helvetica",10); pdf.drawString(40,y,f"{start} to {end}  |  Revenue: {data['revenue']}  |  Expenses: {data['expense_total']}  |  Profit: {data['profit']}"); y-=30
    for b in rows:
        if y<50: pdf.showPage(); y=800
        pdf.drawString(40,y,f"{b.booking_date}  {b.customer.name[:22]}  {b.sport}  {b.amount}  {b.status}"); y-=16
    pdf.save(); response=HttpResponse(output.getvalue(),content_type="application/pdf"); response["Content-Disposition"]='attachment; filename="turfiq-report.pdf"'; return response
