from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
from models.db_models import Template
from models.schemas import TemplateCreate

router = APIRouter(prefix="/templates", tags=["templates"])





@router.get("")
async def list_templates(db: Session = Depends(get_db)):
    """List all templates."""
    templates = db.query(Template).all()
    return templates






@router.post("")
async def create_template(
    name: str = Form(...),
    html_body: str = Form(...),
    db: Session = Depends(get_db)
):
    """Create new template by pasting HTML."""
    db_template = Template(name=name, html_body=html_body)

    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return {"id": db_template.id, "message": "Template saved"}





@router.post("/upload")
async def upload_template(
    file: UploadFile = File(...),
    name: str = Form(...),
    db: Session = Depends(get_db)
):
    """Create new template by uploading HTML file."""
    content = await file.read()
    html_body = content.decode('utf-8')
    
    db_template = Template(name=name, html_body=html_body)
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return {"id": db_template.id, "message": "Template saved"}






@router.put("/{template_id}")
async def update_template(template_id: int, template: dict, db: Session = Depends(get_db)):
    """Update template."""
    db_template = db.query(Template).filter(Template.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if template.get("name"):
        db_template.name = template.get("name")
    if template.get("html_body"):
        db_template.html_body = template.get("html_body")
    
    db.commit()
    return {"message": "Template updated"}







@router.delete("/{template_id}")
async def delete_template(template_id: int, db: Session = Depends(get_db)):
    """Delete template."""
    db_template = db.query(Template).filter(Template.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db.delete(db_template)
    db.commit()
    return {"message": "Template deleted"}    