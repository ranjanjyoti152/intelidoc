# InteliDoc RAG Pipeline

A production-ready Retrieval-Augmented Generation (RAG) pipeline with GPU-accelerated document processing using Docling, vector storage in PostgreSQL (pgvector), and Ollama for local LLM inference.

## 🚀 Features

- **📄 Document Processing**: Upload and process PDFs, DOCX, HTML, Markdown, and more
- **🔍 Vector Search**: Fast similarity search using PostgreSQL pgvector with HNSW indexes
- **🤖 Local LLM**: Fully local AI responses using Ollama (no API keys needed)
- **⚡ GPU Accelerated**: Document parsing and embedding generation leverage NVIDIA GPUs
- **🐳 Docker Ready**: Complete Docker Compose setup with GPU support

## 📋 Prerequisites

- Docker and Docker Compose
- NVIDIA GPU with CUDA support
- NVIDIA Container Toolkit ([Installation Guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html))

Verify GPU support:
```bash
docker run --rm --gpus all nvidia/cuda:12.2-base-ubuntu22.04 nvidia-smi
```

## 🛠️ Quick Start

### 1. Clone and Configure

```bash
cd intelidoc

# Copy environment template
cp .env.example .env

# Edit .env if needed (defaults work out of the box)
```

### 2. Start Services

```bash
# Build and start all services
docker compose up -d --build

# View logs
docker compose logs -f
```

### 3. Pull LLM Model

After Ollama starts, pull the default model:
```bash
docker exec intelidoc-ollama ollama pull llama3.2
```

### 4. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📖 API Usage

### Upload a Document

```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_document.pdf"
```

### Check Document Status

```bash
curl "http://localhost:8000/documents"
```

### Query Your Documents

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the main topic of the document?",
    "top_k": 5
  }'
```

### Vector Search Only

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "specific topic to search",
    "top_k": 10
  }'
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Network                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │   Ollama     │    │   Docling    │    │   PostgreSQL     │  │
│  │   (LLM)      │    │   (Parser)   │    │   + pgvector     │  │
│  │   :11434     │    │   :8001      │    │   :5432          │  │
│  │   [GPU]      │    │   [GPU]      │    │                  │  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
│          ▲                  ▲                     ▲             │
│          │                  │                     │             │
│          └──────────────────┴─────────────────────┘             │
│                             │                                    │
│                    ┌────────┴────────┐                          │
│                    │   RAG API       │                          │
│                    │   (FastAPI)     │                          │
│                    │   :8000         │                          │
│                    │   [GPU]         │                          │
│                    └─────────────────┘                          │
│                             ▲                                    │
└─────────────────────────────┼────────────────────────────────────┘
                              │
                         HTTP/REST
                              │
                        ┌─────┴─────┐
                        │   User    │
                        └───────────┘
```

## 📁 Project Structure

```
intelidoc/
├── docker-compose.yml      # Service orchestration
├── Dockerfile.api          # RAG API service image
├── Dockerfile.docling      # Document processing image
├── init.sql                # PostgreSQL initialization
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template
├── app/                    # Main application
│   ├── main.py             # FastAPI entry point
│   ├── config.py           # Configuration
│   ├── database.py         # Database connection
│   ├── models.py           # SQLAlchemy models
│   ├── schemas.py          # Pydantic schemas
│   ├── routes/
│   │   ├── documents.py    # Document endpoints
│   │   └── query.py        # Query endpoints
│   └── services/
│       ├── docling_client.py  # Docling client
│       ├── embeddings.py      # Embedding service
│       ├── vector_store.py    # Vector operations
│       └── rag_chain.py       # RAG implementation
└── docling_service/        # Document processing microservice
    ├── main.py
    └── requirements.txt
```

## ⚙️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | intelidoc | Database user |
| `POSTGRES_PASSWORD` | intelidoc_secret | Database password |
| `POSTGRES_DB` | intelidoc | Database name |
| `LLM_MODEL` | llama3.2 | Ollama model to use |
| `EMBEDDING_MODEL` | sentence-transformers/all-MiniLM-L6-v2 | Embedding model |
| `CHUNK_SIZE` | 500 | Text chunk size |
| `CHUNK_OVERLAP` | 50 | Overlap between chunks |
| `TOP_K_RESULTS` | 5 | Default number of search results |

## 🔧 Development

### Local Development (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Ollama locally
# ...

# Run the API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Rebuild After Changes

```bash
docker-compose build --no-cache api
docker-compose up -d api
```

## 🐛 Troubleshooting

### GPU Not Detected

```bash
# Verify NVIDIA Container Toolkit
nvidia-ctk --version

# Check Docker GPU support
docker info | grep -i gpu
```

### Model Not Found

```bash
# Pull the required model
docker exec intelidoc-ollama ollama pull llama3.2

# List available models
docker exec intelidoc-ollama ollama list
```

### Database Connection Issues

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Verify pgvector extension
docker exec intelidoc-postgres psql -U intelidoc -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

## 📄 License

MIT License
