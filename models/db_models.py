from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Template(Base):
    """Template table in database."""
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    html_body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class EmailLog(Base):
    """Email sending log table in database."""
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    to_email = Column(String, nullable=False)
    name = Column(String, nullable=True)
    company = Column(String, nullable=True)
    subject = Column(String, nullable=False)
    html_body = Column(Text, nullable=True)
    status = Column(String, nullable=False)  # "sent" or "failed"
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, default=datetime.now)
