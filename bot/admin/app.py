import json
import math
from pathlib import Path

from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from bot.admin.auth import (
    verify_password, create_session, delete_session, is_authenticated,
)
from bot.admin import analytics

BASE_DIR = Path(__file__).parent

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/admin/static", StaticFiles(directory=BASE_DIR / "static"), name="admin_static")

templates = Jinja2Templates(directory=BASE_DIR / "templates")

PER_PAGE = 50


# --- Auth routes ---

@app.get("/admin/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = ""):
    if is_authenticated(request):
        return RedirectResponse("/admin/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": error})


@app.post("/admin/login")
async def login_submit(request: Request, password: str = Form(...)):
    if not verify_password(password):
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Неверный пароль"}, status_code=401,
        )
    token = create_session()
    response = RedirectResponse("/admin/", status_code=302)
    response.set_cookie("admin_session", token, httponly=True, max_age=86400 * 7)
    return response


@app.post("/admin/logout")
async def logout(request: Request):
    token = request.cookies.get("admin_session")
    if token:
        delete_session(token)
    response = RedirectResponse("/admin/login", status_code=302)
    response.delete_cookie("admin_session")
    return response


# --- Auth check middleware-like ---

def _check_auth(request: Request):
    if not is_authenticated(request):
        return RedirectResponse("/admin/login", status_code=302)
    return None


# --- Dashboard ---

@app.get("/admin/", response_class=HTMLResponse)
@app.get("/admin", response_class=HTMLResponse)
async def dashboard(request: Request):
    redirect = _check_auth(request)
    if redirect:
        return redirect

    summary = await analytics.get_summary()
    users_by_day = await analytics.get_users_by_day(30)
    checks_by_day = await analytics.get_checks_by_day(30)
    checks_by_type = await analytics.get_checks_by_type()
    checks_by_color = await analytics.get_checks_by_color()
    leads_by_type = await analytics.get_leads_by_type()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "summary": summary,
        "users_by_day": json.dumps(users_by_day),
        "checks_by_day": json.dumps(checks_by_day),
        "checks_by_type": json.dumps(checks_by_type),
        "checks_by_color": json.dumps(checks_by_color),
        "leads_by_type": json.dumps(leads_by_type),
    })


# --- Users ---

@app.get("/admin/users", response_class=HTMLResponse)
async def users_page(request: Request, page: int = Query(1, ge=1)):
    redirect = _check_auth(request)
    if redirect:
        return redirect

    total = await analytics.count_users()
    total_pages = max(1, math.ceil(total / PER_PAGE))
    offset = (page - 1) * PER_PAGE
    users = await analytics.get_recent_users(PER_PAGE, offset)

    return templates.TemplateResponse("users.html", {
        "request": request,
        "users": users,
        "page": page,
        "total_pages": total_pages,
        "total": total,
    })


# --- Checks ---

@app.get("/admin/checks", response_class=HTMLResponse)
async def checks_page(
    request: Request,
    page: int = Query(1, ge=1),
    input_type: str = Query("", alias="type"),
    result_color: str = Query("", alias="color"),
):
    redirect = _check_auth(request)
    if redirect:
        return redirect

    it = input_type or None
    rc = result_color or None
    total = await analytics.count_checks(it, rc)
    total_pages = max(1, math.ceil(total / PER_PAGE))
    offset = (page - 1) * PER_PAGE
    checks = await analytics.get_recent_checks(PER_PAGE, offset, it, rc)

    return templates.TemplateResponse("checks.html", {
        "request": request,
        "checks": checks,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "filter_type": input_type,
        "filter_color": result_color,
    })


# --- Leads ---

@app.get("/admin/leads", response_class=HTMLResponse)
async def leads_page(
    request: Request,
    page: int = Query(1, ge=1),
    cta_type: str = Query("", alias="cta"),
):
    redirect = _check_auth(request)
    if redirect:
        return redirect

    ct = cta_type or None
    total = await analytics.count_leads(ct)
    total_pages = max(1, math.ceil(total / PER_PAGE))
    offset = (page - 1) * PER_PAGE
    leads = await analytics.get_recent_leads(PER_PAGE, offset, ct)

    return templates.TemplateResponse("leads.html", {
        "request": request,
        "leads": leads,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "filter_cta": cta_type,
    })
