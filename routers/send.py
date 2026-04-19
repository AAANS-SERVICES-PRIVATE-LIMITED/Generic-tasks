from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
from models import ManualSendRequest
from models.db_models import EmailLog
from services import EmailService
import pandas as pd
import io
import csv

router = APIRouter(prefix="/send", tags=["send"])

@router.post("")
async def send_emails(
    email: str = Form(...),
    name: str = Form(None),
    company: str = Form(None),
    subject: str = Form(...),
    html_body: str = Form(None),
    template_name: str = Form(None),
    db: Session = Depends(get_db)
):
    """Send email to single recipient (manual entry)."""
    email_service = EmailService()
    
    # Get HTML body from template or manual input
    if template_name:
        from models.db_models import Template
        template = db.query(Template).filter(Template.name == template_name).first()
        if not template:
            return {"error": "Template not found"}
        html_body = template.html_body
    elif not html_body:
        return {"error": "Either html_body or template_name must be provided"}
    
    result = await email_service.send_single(
        to_email=email,
        subject=subject,
        html_body=html_body
    )
    
    # Log to database
    log = EmailLog(
        to_email=email,
        name=name,
        company=company,
        subject=subject,
        html_body=html_body,
        status=result["status"],
        error_message=result.get("error")
    )
    db.add(log)
    db.commit()
    
    return {
        "total_sent": 1 if result["status"] == "sent" else 0,
        "total_failed": 0 if result["status"] == "sent" else 1,
        "results": [result]
    }


@router.post("/csv")
async def send_emails_csv(
    file: UploadFile = File(...),
    subject: str = Form(...),
    html_body: str = Form(None),
    template_name: str = Form(None),
    db: Session = Depends(get_db)
):
    """Send emails from CSV file upload. Format: email,name,company"""
    email_service = EmailService()
    results = []
    sent = 0
    failed = 0
    
    # Get HTML body from template or manual input
    if template_name:
        from models.db_models import Template
        template = db.query(Template).filter(Template.name == template_name).first()
        if not template:
            return {"error": "Template not found"}
        html_body = template.html_body
    elif not html_body:
        return {"error": "Either html_body or template_name must be provided"}
    
    # Read CSV file
    content = await file.read()
    csv_reader = csv.reader(io.StringIO(content.decode('utf-8')))
    
    # Skip header row
    next(csv_reader, None)
    
    for row in csv_reader:
        if not row:
            continue
        
        # Parse row: email (required), name (optional), company (optional)
        email = row[0].strip() if len(row) > 0 else None
        name = row[1].strip() if len(row) > 1 else None
        company = row[2].strip() if len(row) > 2 else None
        
        # Validate email
        if not email or '@' not in email:
            results.append({"email": email or "missing", "status": "failed", "error": "Invalid or missing email"})
            failed += 1
            continue
        
        # Send email
        result = await email_service.send_single(
            to_email=email,
            subject=subject,
            html_body=html_body
        )
        results.append(result)
        
        # Log to database
        log = EmailLog(
            to_email=email,
            name=name,
            company=company,
            subject=subject,
            html_body=html_body,
            status=result["status"],
            error_message=result.get("error")
        )
        db.add(log)
        db.commit()
        
        if result["status"] == "sent":
            sent += 1
        else:
            failed += 1
    
    return {
        "total_sent": sent,
        "total_failed": failed,
        "results": results
    }


@router.post("/xlsx")
async def send_emails_xlsx(
    file: UploadFile = File(...),
    subject: str = Form(...),
    html_body: str = Form(None),
    template_name: str = Form(None),
    db: Session = Depends(get_db)
):
    """Send emails from XLSX file upload. Format: email,name,company"""
    email_service = EmailService()
    results = []
    sent = 0
    failed = 0
    
    # Get HTML body from template or manual input
    if template_name:
        from models.db_models import Template
        template = db.query(Template).filter(Template.name == template_name).first()
        if not template:
            return {"error": "Template not found"}
        html_body = template.html_body
    elif not html_body:
        return {"error": "Either html_body or template_name must be provided"}
    
    # Read XLSX file
    content = await file.read()
    df = pd.read_excel(io.BytesIO(content))
    
    for _, row in df.iterrows():
        # Parse row: email (required), name (optional), company (optional)
        email = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else None
        name = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else None
        company = str(row.iloc[2]).strip() if len(row) > 2 and pd.notna(row.iloc[2]) else None
        
        # Validate email
        if not email or '@' not in email or email == 'nan':
            results.append({"email": email or "missing", "status": "failed", "error": "Invalid or missing email"})
            failed += 1
            continue
        
        # Send email
        result = await email_service.send_single(
            to_email=email,
            subject=subject,
            html_body=html_body
        )
        results.append(result)
        
        # Log to database
        log = EmailLog(
            to_email=email,
            name=name,
            company=company,
            subject=subject,
            html_body=html_body,
            status=result["status"],
            error_message=result.get("error")
        )
        db.add(log)
        db.commit()
        
        if result["status"] == "sent":
            sent += 1
        else:
            failed += 1
    
    return {
        "total_sent": sent,
        "total_failed": failed,
        "results": results
    }