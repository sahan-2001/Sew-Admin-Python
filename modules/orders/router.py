from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def get_orders(request: Request):
    return templates.TemplateResponse("orders.html", {"request": request})

@router.post("/")
def create_order():
    return {"message": "Order created"}
