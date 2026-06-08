from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from datetime import datetime
from database import Base


class FileRecord(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    storage_path = Column(Text, nullable=False)

    upload_time = Column(DateTime, default=datetime.utcnow, nullable=False)

    extracted_text = Column(Text, nullable=True)

    summary = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    tags = Column(JSON, nullable=True)

    recommend_score = Column(Integer, default=0, nullable=False)
    pros = Column(JSON, nullable=True)
    cons = Column(JSON, nullable=True)

    status = Column(String(50), default="uploaded", nullable=False)
