from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def get_products(request: Request):
    return templates.TemplateResponse("products.html", {"request": request})

@router.post("/")
def create_product():
    return {"message": "Product created"}
