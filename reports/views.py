import csv
from io import BytesIO
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from openpyxl import Workbook
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
        for b in rows: ws.append([b.booking_date,b.customer.name,b.customer.phone,b.sport,b.ground,float(b.amount),b.payment_method,b.status])
        output=BytesIO(); wb.save(output); response=HttpResponse(output.getvalue(),content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"); response["Content-Disposition"]='attachment; filename="turfiq-report.xlsx"'; return response
    output=BytesIO(); pdf=canvas.Canvas(output,pagesize=A4); y=800; pdf.setFont("Helvetica-Bold",16); pdf.drawString(40,y,"TurfIQ Analytics Report"); y-=28; pdf.setFont("Helvetica",10); pdf.drawString(40,y,f"{start} to {end}  |  Revenue: {data['revenue']}  |  Expenses: {data['expense_total']}  |  Profit: {data['profit']}"); y-=30
    for b in rows:
        if y<50: pdf.showPage(); y=800
        pdf.drawString(40,y,f"{b.booking_date}  {b.customer.name[:22]}  {b.sport}  {b.amount}  {b.status}"); y-=16
    pdf.save(); response=HttpResponse(output.getvalue(),content_type="application/pdf"); response["Content-Disposition"]='attachment; filename="turfiq-report.pdf"'; return response
