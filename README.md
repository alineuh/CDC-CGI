# 📊 Intelligent Payslip Analysis System

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)

## 🎯 Project Overview

AI-powered system for analyzing French payslips, detecting anomalies, and calculating severance costs.

**R&D Project for CEGI - ESILV A5 Apprentice Track**

### Key Features
- 🔍 **PDF Data Extraction**: Automated parsing of payslip PDFs
- 🤖 **AI Classification**: ML-based valid/invalid detection
- 📊 **Error Detection**: Identification and explanation of anomalies
- 💰 **Severance Calculator**: Automated cost calculation for various scenarios
- 🌐 **Web Interface**: User-friendly dashboard
- 🔌 **REST API**: Easy integration capabilities

## 🛠 Tech Stack

- **Backend**: Python 3.11+, FastAPI
- **ML/AI**: PyTorch, scikit-learn, Transformers
- **PDF Processing**: pdfplumber, PyPDF2, Tesseract OCR
- **Database**: PostgreSQL
- **Frontend**: React
- **Deployment**: Docker, Docker Compose

## 📋 Prerequisites

- Python 3.11 or higher
- Docker & Docker Compose
- Git
- 4GB RAM minimum

## ⚙️ Quick Start
```bash
# Clone the repository
git clone git@github.com:alineuh/CDC-CGI.git
cd CDC-CGI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Run with Docker
docker-compose up -d

# Access the application
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
# UI: http://localhost:3000
```

## 📁 Project Structure
```
CDC-CGI/
├── docs/               # Documentation
├── data/              # Data files
│   ├── valid/         # Valid payslips
│   ├── invalid/       # Invalid payslips
│   └── samples/       # Test samples
├── src/               # Source code
│   ├── extraction/    # PDF extraction module
│   ├── classifier/    # Classification model
│   ├── calculator/    # Severance calculator
│   ├── api/          # API endpoints
│   └── ui/           # Frontend
├── tests/            # Test suites
├── models/           # Trained models
├── notebooks/        # Jupyter notebooks
└── scripts/          # Utility scripts
```

## 🧪 Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test suite
pytest tests/unit/test_extraction.py
```

## 📚 Documentation

- [Architecture Overview](docs/architecture.md)
- [Data Flow Diagram](docs/data-flow.md)
- [API Documentation](docs/api-documentation.md)
- [Development Guide](docs/development.md)

## 🎯 Project Deliverables

- ✅ Source code (structured Git repository)
- ✅ Functional web interface (deployed)
- ✅ Technical documentation
- ✅ Oral presentation with demo

## 📊 Evaluation Criteria

- **Technical Robustness** (30%): Success rate on test scenarios
- **Explainability** (25%): Clear error explanations and traceability
- **User Interface** (15%): Intuitive and responsive design
- **Code Quality** (20%): Documentation, testing, structure
- **Innovation** (10%): Original approach and features

## 👥 Team Members

| Name | Role | GitHub |
|------|------|--------|
| TBD | Project Lead | [@username] |
| TBD | ML Engineer | [@username] |
| TBD | Backend Dev | [@username] |
| TBD | Frontend Dev | [@username] |
| TBD | DevOps | [@username] |

## 📅 Project Timeline

- **Day 1 (Monday)**: Architecture & PDF Extraction
- **Day 2 (Tuesday)**: Classification Model
- **Day 3 (Wednesday)**: Business Logic & Calculations
- **Day 4 (Thursday)**: Integration & API
- **Day 5 (Friday)**: Presentation & Demo

## 🤝 Contributing

1. Create a feature branch (`git checkout -b feature/AmazingFeature`)
2. Commit your changes (`git commit -m 'feat: Add some AmazingFeature'`)
3. Push to the branch (`git push origin feature/AmazingFeature`)
4. Open a Pull Request

### Branch Naming Convention
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions

### Commit Message Convention
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Formatting
- `refactor:` - Code restructuring
- `test:` - Adding tests
- `chore:` - Maintenance

## 📝 License

Proprietary - CEGI © 2026

## 📧 Contact

Project Link: [https://github.com/alineuh/CDC-CGI](https://github.com/alineuh/CDC-CGI)

---

**ESILV - École Supérieure d'Ingénieurs Léonard de Vinci**  
Research & Development Module - A5 Apprentice Track
