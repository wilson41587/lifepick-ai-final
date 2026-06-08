# LifePick AI Final Project

LifePick AI 是一個部署在 Kubernetes 上的 AI 生活資料整理與推薦系統。使用者可以上傳 PDF / TXT 檔案，系統會自動產生摘要、分類、標籤與推薦分數。

## 1. Features

- Upload PDF / TXT files
- Extract text from uploaded files
- Generate summary, category, tags, and recommendation score
- Store original files in MinIO
- Store metadata and analysis results in PostgreSQL
- Search uploaded documents by keyword
- React frontend
- FastAPI backend
- Docker Compose deployment
- Kubernetes deployment with LoadBalancer

## 2. System Architecture

```text
Browser
  |
  v
Frontend LoadBalancer
  |
  v
Frontend Nginx
  |
  |-- Static React UI
  |
  '-- /api proxy
        |
        v
Backend Service
  |
  |-- PostgreSQL: metadata and AI analysis results
  |
  '-- MinIO: original uploaded files
```

## 3. Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, Nginx |
| Backend | FastAPI, Python |
| Database | PostgreSQL |
| Object Storage | MinIO |
| Container | Docker, Docker Compose |
| Orchestration | Kubernetes |
| External Access | LoadBalancer / MetalLB |

## 4. Docker Images

```text
wilson41587/lifepick-backend:v1
wilson41587/lifepick-frontend:k8s
```

## 5. Run with Docker Compose

```bash
docker compose up -d --build
```

Frontend:

```text
http://172.16.225.129:5173
```

Backend health check:

```bash
curl http://localhost:8000/health
```

MinIO Console:

```text
http://172.16.225.129:9001
```

Default MinIO login:

```text
username: minioadmin
password: minioadmin
```

## 6. Deploy to Kubernetes

Apply all Kubernetes resources:

```bash
kubectl apply -f k8s/final-all.yaml
```

Check resources:

```bash
kubectl get pods -n final -o wide
kubectl get svc -n final
kubectl get pvc -n final
```

Open the external IP of the frontend LoadBalancer in the browser.

## 7. Demo Commands

Check cluster nodes:

```bash
kubectl get nodes -o wide
```

Check application pods:

```bash
kubectl get pods -n final -o wide
```

Check services:

```bash
kubectl get svc -n final
```

Check persistent volumes:

```bash
kubectl get pvc -n final
```

Scale backend:

```bash
kubectl scale deployment backend -n final --replicas=3
kubectl get pods -n final -o wide
```

Scale backend back to one replica:

```bash
kubectl scale deployment backend -n final --replicas=1
```

Show backend logs:

```bash
kubectl logs deployment/backend -n final
```

Test self-healing:

```bash
kubectl get pods -n final
kubectl delete pod <backend-pod-name> -n final
kubectl get pods -n final -w
```

Check PostgreSQL data:

```bash
kubectl exec -it deployment/postgres -n final -- psql -U lifepick -d lifepick
```

Inside psql:

```sql
SELECT id, file_name, storage_path, category, recommend_score, status
FROM files
ORDER BY id DESC
LIMIT 5;
```

Exit psql:

```sql
\q
```

## 8. Demo Files

Recommended demo files:

- demo_food.txt
- demo_headphone.txt
- demo_travel.txt

Example keywords for search:

```text
學生
台中
聚餐
耳機
續航
旅遊
景點
```

## 9. Current Status

The MVP version is completed and deployable on Kubernetes.

Completed:

- Frontend UI
- Backend API
- PDF / TXT upload
- Text extraction
- Summary, category, tags, and recommendation score generation
- PostgreSQL integration
- MinIO integration
- Docker Compose deployment
- Docker Hub image push
- Kubernetes deployment
- LoadBalancer access
- Upload / analysis / search demo

## 10. Future Work

- Real LLM API integration
- Independent AI Worker
- Async queue for background analysis
- OCR for image and scanned PDF files
- Semantic search with embeddings
- User login and authorization
- HPA autoscaling
- CI/CD pipeline
