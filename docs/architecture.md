# System Architecture

## Overview

The Payslip Analyzer follows a Service-Oriented Architecture (SOA) with clear separation of concerns.

## Architecture Diagram
```
┌─────────────┐
│   Frontend  │
│   (React)   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  REST API   │
│  (FastAPI)  │
└──────┬──────┘
       │
       ├─────────────┬─────────────┬─────────────┐
       ▼             ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│Extraction│  │Classifier│  │Calculator│  │ Database │
│  Module  │  │  Module  │  │  Module  │  │(Postgres)│
└──────────┘  └──────────┘  └──────────┘  └──────────┘
       │             │             │
       ▼             ▼             ▼
┌──────────────────────────────────────┐
│       External Services              │
│  - LLM API                          │
│  - Embedding Engine                 │
└──────────────────────────────────────┘
```

## Components

### 1. Extraction Module (`src/extraction/`)
- **Purpose**: Parse PDF payslips and extract structured data
- **Technologies**: pdfplumber, PyPDF2, Tesseract OCR
- **Output**: Structured JSON with payslip fields

### 2. Classifier Module (`src/classifier/`)
- **Purpose**: Classify payslips as valid/invalid and identify errors
- **Technologies**: scikit-learn, PyTorch, Transformers
- **Output**: Classification result with confidence scores

### 3. Calculator Module (`src/calculator/`)
- **Purpose**: Calculate severance costs based on scenarios
- **Technologies**: Python, NumPy, pandas
- **Input**: Valid payslip data + scenario parameters
- **Output**: Detailed cost breakdown

### 4. API Layer (`src/api/`)
- **Purpose**: Expose functionality via REST endpoints
- **Technologies**: FastAPI, Pydantic
- **Features**: Authentication, validation, documentation

### 5. Database
- **Purpose**: Store payslips, results, and user data
- **Technologies**: PostgreSQL, SQLAlchemy
- **Schema**: Users, Payslips, Classifications, Calculations

## Data Flow

1. User uploads PDF via UI
2. API receives file and calls Extraction Module
3. Extracted data is validated and stored
4. Classifier Module analyzes the payslip
5. If valid, Calculator Module can process scenarios
6. Results are stored and returned to user
7. UI displays results with explanations

## Security Considerations

- API authentication via JWT tokens
- Input validation at all entry points
- Secure file upload handling
- Database connection encryption
- Sensitive data encryption at rest

## Scalability

- Stateless API design
- Horizontal scaling via Docker/Kubernetes
- Async processing for long-running tasks
- Caching layer for frequent queries
