from fastapi import APIRouter
from .dsb import router as dsb_router

router = APIRouter()

router.include_router(dsb_router, prefix="/dsb", tags=["DSB Stundenplan"])
