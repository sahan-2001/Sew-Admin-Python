from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def get_customers(request: Request):
    return templates.TemplateResponse("customers.html", {"request": request})

@router.post("/")
def create_customer():
    return {"message": "Customer created"}
