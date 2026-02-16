from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Payslip Analyzer API",
    description="API for analyzing French payslips and calculating severance costs",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Payslip Analyzer API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# TODO: Add routes for:
# - POST /api/v1/payslips/upload
# - POST /api/v1/payslips/classify
# - POST /api/v1/payslips/calculate
# - GET /api/v1/payslips/{id}
