# 1. 呼叫 LLM API
# 2. 產生摘要
# 3. 分類文件
# 4. 自動產生 tags
# 5. 產生推薦理由、注意事項、推薦分數


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

client = OpenAI(api_key=OPENAI_API_KEY)

def call_llm_api(text: str) -> Dict[str, Any]:
    # 這裡是呼叫 LLM API 的邏輯，根據實際使用的 LLM 服務進行調整
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that analyzes documents."},
            {"role": "user", "content": f"Analyze the following text and provide a summary, category, tags, recommendation score, pros, and cons:\n\n{text}"}
        ],
        max_tokens=1000,
        temperature=0.7,
    )
    
    # 假設 LLM 回傳的格式如下，根據實際回傳格式進行調整
    result = response.choices[0].message.content
    return {
        "summary": result.get("summary", ""),
        "category": result.get("category", ""),
        "tags": result.get("tags", []),
        "recommend_score": result.get("recommend_score", 0),
        "pros": result.get("pros", []),
        "cons": result.get("cons", []),
    }
