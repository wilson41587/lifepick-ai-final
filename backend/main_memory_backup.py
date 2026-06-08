from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import shutil
import fitz  # PyMuPDF


app = FastAPI(
    title="LifePick AI Backend",
    description="AI life document analysis backend for cloud final project",
    version="0.1.0",
)

# 先全部允許，方便前端開發。正式環境再收斂來源。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# MVP 第一版先用記憶體暫存，下一階段會換成 PostgreSQL。
FILES: Dict[int, Dict[str, Any]] = {}
NEXT_ID = 1


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text from a text-based PDF."""
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
    """Extract text from TXT file."""
    try:
        return file_path.read_text(encoding="utf-8").strip()
    except UnicodeDecodeError:
        return file_path.read_text(encoding="latin-1").strip()


def extract_text(file_path: Path, file_type: str) -> str:
    """Route file to proper text extractor."""
    if file_type == "pdf":
        return extract_text_from_pdf(file_path)

    if file_type == "txt":
        return extract_text_from_txt(file_path)

    return ""


def analyze_text(text: str) -> Dict[str, Any]:
    """
    Fake AI analyzer for MVP.
    Later we will replace this with real AI API.
    """
    lowered = text.lower()

    category = "一般資料"
    tags = []
    pros = []
    cons = ["資料可能需要進一步確認或更新"]
    score = 70

    # 美食類
    food_keywords = ["餐廳", "美食", "聚餐", "火鍋", "義大利麵", "平價", "學生", "咖啡"]
    if any(k in text for k in food_keywords):
        category = "美食推薦"
        tags.extend(["美食", "餐廳", "聚餐"])
        pros.extend(["適合生活決策", "內容包含餐廳或聚餐資訊"])
        score += 10

    if "學生" in text or "平價" in text:
        tags.extend(["學生", "平價"])
        pros.append("適合學生族群或預算有限的使用者")
        score += 5

    if "台中" in text:
        tags.append("台中")
        score += 3

    # 商品心得類
    product_keywords = ["耳機", "音質", "續航", "降噪", "cp值", "商品", "心得"]
    if any(k in lowered for k in product_keywords) or any(k in text for k in product_keywords):
        category = "商品心得"
        tags.extend(["商品", "心得", "CP值"])
        pros.append("內容包含產品使用心得")
        score += 8

    if "耳機" in text:
        tags.append("藍牙耳機")

    # 旅遊類
    travel_keywords = ["旅遊", "景點", "行程", "交通", "台南", "住宿"]
    if any(k in text for k in travel_keywords):
        category = "旅遊行程"
        tags.extend(["旅遊", "景點", "行程"])
        pros.append("內容包含旅遊規劃資訊")
        score += 8

    # 去除重複 tag
    tags = list(dict.fromkeys(tags))

    if not tags:
        tags = ["文件", "生活資料"]

    if not pros:
        pros = ["可以快速整理文件重點"]

    # 摘要先取前 120 字，下一階段再接 AI API。
    clean_text = " ".join(text.split())
    if clean_text:
        summary = clean_text[:120]
        if len(clean_text) > 120:
            summary += "..."
    else:
        summary = "目前無法從此檔案擷取文字內容。"

    score = max(0, min(score, 100))

    return {
        "summary": summary,
        "category": category,
        "tags": tags,
        "recommend_score": score,
        "pros": pros,
        "cons": cons,
    }


@app.get("/")
def root():
    return {
        "message": "LifePick AI Backend is running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "lifepick-backend",
        "time": datetime.utcnow().isoformat(),
    }


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global NEXT_ID

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    suffix = Path(file.filename).suffix.lower().replace(".", "")
    if suffix not in ["pdf", "txt"]:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported in MVP version",
        )

    file_id = NEXT_ID
    NEXT_ID += 1

    saved_name = f"{file_id}_{file.filename}"
    saved_path = UPLOAD_DIR / saved_name

    try:
        with saved_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File save failed: {e}")

    try:
        extracted_text = extract_text(saved_path, suffix)
        analysis = analyze_text(extracted_text)
        status = "completed"
    except Exception as e:
        extracted_text = ""
        analysis = {
            "summary": "檔案已上傳，但分析失敗。",
            "category": "分析失敗",
            "tags": ["failed"],
            "recommend_score": 0,
            "pros": [],
            "cons": [str(e)],
        }
        status = "failed"

    record = {
        "id": file_id,
        "file_name": file.filename,
        "file_type": suffix,
        "storage_path": str(saved_path),
        "upload_time": datetime.utcnow().isoformat(),
        "extracted_text": extracted_text,
        "summary": analysis["summary"],
        "category": analysis["category"],
        "tags": analysis["tags"],
        "recommend_score": analysis["recommend_score"],
        "pros": analysis["pros"],
        "cons": analysis["cons"],
        "status": status,
    }

    FILES[file_id] = record

    return record


@app.get("/files")
def get_files():
    results = []

    for item in FILES.values():
        results.append({
            "id": item["id"],
            "file_name": item["file_name"],
            "file_type": item["file_type"],
            "upload_time": item["upload_time"],
            "category": item["category"],
            "tags": item["tags"],
            "recommend_score": item["recommend_score"],
            "status": item["status"],
        })

    return results


@app.get("/files/{file_id}")
def get_file(file_id: int):
    if file_id not in FILES:
        raise HTTPException(status_code=404, detail="File not found")

    return FILES[file_id]


@app.delete("/files/{file_id}")
def delete_file(file_id: int):
    if file_id not in FILES:
        raise HTTPException(status_code=404, detail="File not found")

    record = FILES[file_id]
    path = Path(record["storage_path"])

    if path.exists():
        path.unlink()

    del FILES[file_id]

    return {
        "message": "File deleted",
        "file_id": file_id,
    }


@app.get("/search")
def search_files(q: str = Query(..., description="Search keyword")):
    keyword = q.lower()
    results = []

    for item in FILES.values():
        searchable_text = " ".join([
            item.get("file_name", ""),
            item.get("summary", ""),
            item.get("category", ""),
            " ".join(item.get("tags", [])),
            " ".join(item.get("pros", [])),
            " ".join(item.get("cons", [])),
            item.get("extracted_text", ""),
        ]).lower()

        if keyword in searchable_text:
            results.append({
                "id": item["id"],
                "file_name": item["file_name"],
                "file_type": item["file_type"],
                "summary": item["summary"],
                "category": item["category"],
                "tags": item["tags"],
                "recommend_score": item["recommend_score"],
                "status": item["status"],
            })

    return results
