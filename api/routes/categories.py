from api.schemas import CategoryParent
from api.services.category_loader import build_category_tree
from fastapi import APIRouter

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryParent])
def get_categories():
    return build_category_tree()
