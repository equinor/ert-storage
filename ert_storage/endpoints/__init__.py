from fastapi import APIRouter
from .ensembles import router as ensembles_router
from .records import router as records_router
from .experiments import router as experiments_router


router = APIRouter()
router.include_router(experiments_router)
router.include_router(ensembles_router)
router.include_router(records_router)
