import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function App() {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadFile, setUploadFile] = useState(null);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const fetchFiles = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/files`);
      setFiles(res.data);
    } catch (err) {
      console.error(err);
      setMessage("無法取得檔案列表，請確認 Backend 是否啟動。");
    }
  };

  const fetchFileDetail = async (id) => {
    try {
      const res = await axios.get(`${API_BASE_URL}/files/${id}`);
      setSelectedFile(res.data);
    } catch (err) {
      console.error(err);
      setMessage("無法取得檔案詳細資料。");
    }
  };

  const handleUpload = async () => {
    if (!uploadFile) {
      setMessage("請先選擇 PDF 或 TXT 檔案。");
      return;
    }

    const formData = new FormData();
    formData.append("file", uploadFile);

    try {
      setLoading(true);
      setMessage("檔案上傳與分析中...");

      const res = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setSelectedFile(res.data);
      setUploadFile(null);
      setMessage("上傳與分析完成。");
      await fetchFiles();
    } catch (err) {
      console.error(err);
      const detail =
        err.response?.data?.detail || "上傳失敗，請確認檔案格式或 Backend 狀態。";
      setMessage(detail);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchKeyword.trim()) {
      setMessage("請輸入搜尋關鍵字。");
      return;
    }

    try {
      const res = await axios.get(`${API_BASE_URL}/search`, {
        params: {
          q: searchKeyword,
        },
      });

      setSearchResults(res.data);
      setMessage(`搜尋完成，共找到 ${res.data.length} 筆結果。`);
    } catch (err) {
      console.error(err);
      setMessage("搜尋失敗。");
    }
  };

  const handleDelete = async (id) => {
    const ok = window.confirm("確定要刪除這個檔案嗎？");
    if (!ok) return;

    try {
      await axios.delete(`${API_BASE_URL}/files/${id}`);
      setMessage("檔案已刪除。");

      if (selectedFile?.id === id) {
        setSelectedFile(null);
      }

      await fetchFiles();
      setSearchResults((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      console.error(err);
      setMessage("刪除失敗。");
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>LifePick AI</h1>
          <p>AI 生活資料整理與推薦系統</p>
        </div>
        <div className="api-badge">Backend: {API_BASE_URL}</div>
      </header>

      {message && <div className="message">{message}</div>}

      <main className="grid">
        <section className="card">
          <h2>1. 上傳檔案</h2>
          <p className="hint">
            支援 PDF / TXT。系統會自動摘要、分類、標籤化與產生推薦分數。
          </p>

          <input
            type="file"
            accept=".pdf,.txt"
            onChange={(e) => setUploadFile(e.target.files[0])}
          />

          {uploadFile && (
            <p className="selected-name">已選擇：{uploadFile.name}</p>
          )}

          <button onClick={handleUpload} disabled={loading}>
            {loading ? "分析中..." : "上傳並分析"}
          </button>
        </section>

        <section className="card">
          <h2>2. 智慧搜尋</h2>
          <p className="hint">例如：學生、台中、聚餐、耳機、旅遊。</p>

          <div className="search-row">
            <input
              type="text"
              value={searchKeyword}
              placeholder="輸入搜尋關鍵字"
              onChange={(e) => setSearchKeyword(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSearch();
              }}
            />
            <button onClick={handleSearch}>搜尋</button>
          </div>

          <div className="result-list">
            {searchResults.map((item) => (
              <div className="mini-item" key={item.id}>
                <div onClick={() => fetchFileDetail(item.id)}>
                  <strong>{item.file_name}</strong>
                  <p>{item.summary}</p>
                  <span>{item.category}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="card file-list-card">
          <h2>3. 檔案列表</h2>

          {files.length === 0 ? (
            <p className="hint">目前尚未上傳檔案。</p>
          ) : (
            <div className="file-list">
              {files.map((file) => (
                <div
                  className={`file-item ${
                    selectedFile?.id === file.id ? "active" : ""
                  }`}
                  key={file.id}
                >
                  <div onClick={() => fetchFileDetail(file.id)}>
                    <strong>{file.file_name}</strong>
                    <p>
                      {file.category || "未分類"} · 分數{" "}
                      {file.recommend_score}
                    </p>
                    <div className="tag-row">
                      {(file.tags || []).map((tag) => (
                        <span className="tag" key={tag}>
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>

                  <button
                    className="delete-btn"
                    onClick={() => handleDelete(file.id)}
                  >
                    刪除
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="card detail-card">
          <h2>4. AI 分析結果</h2>

          {!selectedFile ? (
            <p className="hint">請上傳檔案或從檔案列表選擇一筆資料。</p>
          ) : (
            <div className="detail">
              <div className="detail-title">
                <h3>{selectedFile.file_name}</h3>
                <span className="score">{selectedFile.recommend_score}</span>
              </div>

              <div className="info-row">
                <span>分類</span>
                <strong>{selectedFile.category}</strong>
              </div>

              <div className="tag-row">
                {(selectedFile.tags || []).map((tag) => (
                  <span className="tag" key={tag}>
                    {tag}
                  </span>
                ))}
              </div>

              <h4>摘要</h4>
              <p className="summary">{selectedFile.summary}</p>

              <h4>推薦理由 / 優點</h4>
              <ul>
                {(selectedFile.pros || []).map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>

              <h4>限制 / 注意事項</h4>
              <ul>
                {(selectedFile.cons || []).map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>

              <h4>儲存位置</h4>
              <code>{selectedFile.storage_path}</code>

              <h4>狀態</h4>
              <span className={`status ${selectedFile.status}`}>
                {selectedFile.status}
              </span>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
