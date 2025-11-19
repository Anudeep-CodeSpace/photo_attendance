from fastapi import APIRouter, Depends
from app.dependencies import verify_api_key
router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "200", "message": "Backend running"}

@router.get("/verify")
def verify_service(authorized: bool = Depends(verify_api_key)):
    if authorized:
        return {"status": "200", "message": "API key valid"}
    else:
        return {"status": "401", "message": "Invalid API key"}