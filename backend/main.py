from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import shutil
import fitz  # PyMuPDF

from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import FileRecord
from storage import ensure_bucket, upload_file_to_minio, delete_file_from_minio


app = FastAPI(
    title="LifePick AI Backend",
    description="AI life document analysis backend for cloud final project",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    ensure_bucket()


def extract_text_from_pdf(file_path: Path) -> str:
    text_parts = []

    try:
        doc = fitz.open(file_path)
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
    except Exception as e:
        raise RuntimeError(f"PDF text extraction failed: {e}")

    return "\n".join(text_parts).strip()


def extract_text_from_txt(file_path: Path) -> str:
    try:
        return file_path.read_text(encoding="utf-8").strip()
    except UnicodeDecodeError:
        return file_path.read_text(encoding="latin-1").strip()


def extract_text(file_path: Path, file_type: str) -> str:
    if file_type == "pdf":
        return extract_text_from_pdf(file_path)

    if file_type == "txt":
        return extract_text_from_txt(file_path)

    return ""


def analyze_text(text: str) -> Dict[str, Any]:
    lowered = text.lower()
    # Call API to get real analysis results. For now, we return dummy data based on keyword matching.
    # LLM 回傳 summary / category / tags / score / pros / cons

    
    return {
        "summary": summary,
        "category": category,
        "tags": tags,
        "recommend_score": score,
        "pros": pros,
        "cons": cons,
    }


def record_to_dict(record: FileRecord) -> Dict[str, Any]:
    return {
        "id": record.id,
        "file_name": record.file_name,
        "file_type": record.file_type,
        "storage_path": record.storage_path,
        "upload_time": record.upload_time.isoformat() if record.upload_time else None,
        "extracted_text": record.extracted_text,
        "summary": record.summary,
        "category": record.category,
        "tags": record.tags or [],
        "recommend_score": record.recommend_score,
        "pros": record.pros or [],
        "cons": record.cons or [],
        "status": record.status,
    }


def record_to_list_item(record: FileRecord) -> Dict[str, Any]:
    return {
        "id": record.id,
        "file_name": record.file_name,
        "file_type": record.file_type,
        "upload_time": record.upload_time.isoformat() if record.upload_time else None,
        "category": record.category,
        "tags": record.tags or [],
        "recommend_score": record.recommend_score,
        "status": record.status,
    }


@app.get("/")
def root():
    return {
        "message": "LifePick AI Backend is running",
        "docs": "/docs",
        "version": "0.3.0-postgresql-minio",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "lifepick-backend",
        "time": datetime.utcnow().isoformat(),
    }


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    suffix = Path(file.filename).suffix.lower().replace(".", "")
    if suffix not in ["pdf", "txt"]:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported in MVP version",
        )

    # 先建立 DB record，拿到 id 後再用 id 組檔名。
    record = FileRecord(
        file_name=file.filename,
        file_type=suffix,
        storage_path="pending",
        status="uploaded",
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    saved_name = f"{record.id}_{file.filename}"
    saved_path = UPLOAD_DIR / saved_name

    try:
        with saved_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        record.status = "failed"
        record.cons = [f"File save failed: {e}"]
        db.commit()
        raise HTTPException(status_code=500, detail=f"File save failed: {e}")

    try:
        extracted_text = extract_text(saved_path, suffix)
        analysis = analyze_text(extracted_text)

        object_name = f"uploads/{record.id}_{file.filename}"
        storage_path = upload_file_to_minio(saved_path, object_name)

        record.storage_path = storage_path
        record.extracted_text = extracted_text
        record.summary = analysis["summary"]
        record.category = analysis["category"]
        record.tags = analysis["tags"]
        record.recommend_score = analysis["recommend_score"]
        record.pros = analysis["pros"]
        record.cons = analysis["cons"]
        record.status = "completed"

    except Exception as e:
        record.storage_path = str(saved_path)
        record.extracted_text = ""
        record.summary = "檔案已上傳，但分析失敗。"
        record.category = "分析失敗"
        record.tags = ["failed"]
        record.recommend_score = 0
        record.pros = []
        record.cons = [str(e)]
        record.status = "failed"

    db.commit()
    db.refresh(record)

    return record_to_dict(record)


@app.get("/files")
def get_files(db: Session = Depends(get_db)):
    records = db.query(FileRecord).order_by(FileRecord.id.desc()).all()
    return [record_to_list_item(record) for record in records]


@app.get("/files/{file_id}")
def get_file(
    file_id: int,
    db: Session = Depends(get_db),
):
    record = db.query(FileRecord).filter(FileRecord.id == file_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="File not found")

    return record_to_dict(record)


@app.delete("/files/{file_id}")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
):
    record = db.query(FileRecord).filter(FileRecord.id == file_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="File not found")

    delete_file_from_minio(record.storage_path)

    # If a local cached file still exists, remove it as well.
    local_cache = UPLOAD_DIR / f"{record.id}_{record.file_name}"
    if local_cache.exists():
        local_cache.unlink()

    db.delete(record)
    db.commit()

    return {
        "message": "File deleted",
        "file_id": file_id,
    }


@app.get("/search")
def search_files(
    q: str = Query(..., description="Search keyword"),
    db: Session = Depends(get_db),
):
    keyword = q.lower()
    records = db.query(FileRecord).order_by(FileRecord.id.desc()).all()

    results = []

    for record in records:
        searchable_text = " ".join([
            record.file_name or "",
            record.summary or "",
            record.category or "",
            " ".join(record.tags or []),
            " ".join(record.pros or []),
            " ".join(record.cons or []),
            record.extracted_text or "",
        ]).lower()

        if keyword in searchable_text:
            results.append({
                "id": record.id,
                "file_name": record.file_name,
                "file_type": record.file_type,
                "summary": record.summary,
                "category": record.category,
                "tags": record.tags or [],
                "recommend_score": record.recommend_score,
                "status": record.status,
            })

    return results
