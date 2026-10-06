"""前后端分离计算器 —— 后端 API（FastAPI）。

接口：
- GET    /api/health              健康检查
- POST   /api/calculate           计算表达式（save=true 写入历史，false 仅预览）
- GET    /api/history             历史记录（分页 + 搜索）
- DELETE /api/history             清空全部历史
- DELETE /api/history/{record_id} 删除指定记录
- GET    /api/info                返回局域网访问地址（供手机）
- GET    /api/qr                  返回手机访问地址的二维码（SVG）

同时以静态文件方式托管前端（frontend/）。
"""
from __future__ import annotations

import html
import json
import os
import socket
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db import CalculationHistory, SessionLocal, init_db, serialize_dt, utc_now
from evaluator import ExpressionError, evaluate, format_result

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))


def _lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


LAN_URL = f"http://{_lan_ip()}:8000/"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="前后端分离计算器", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CalculateRequest(BaseModel):
    expression: str = Field(..., min_length=1, max_length=200)
    save: bool = True  # 实时预览时为 False，不写入历史


class CalculateResponse(BaseModel):
    expression: str
    result: str
    record_id: int | None = None
    created_at: str | None = None


class HistoryItem(BaseModel):
    id: int
    expression: str
    result: str
    created_at: str


class HistoryResponse(BaseModel):
    items: list[HistoryItem]
    total: int
    page: int
    page_size: int


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"status": "ok"}


@app.get("/api/info")
def info():
    return {"lan_url": LAN_URL}


@app.get("/api/qr")
def qr():
    import qrcode

    q = qrcode.QRCode(border=1)
    q.add_data(LAN_URL)
    q.make(fit=True)
    m = q.get_matrix()
    return Response(_matrix_to_svg(m), media_type="image/svg+xml")


def _matrix_to_svg(matrix, box=8):
    """把 qrcode 生成的布尔矩阵渲染为 SVG 字符串（无需 Pillow）。"""
    n = len(matrix)
    total = n + 2
    size = total * box
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {total} {total}" shape-rendering="crispEdges">',
        f'<rect width="{total}" height="{total}" fill="#ffffff"/>',
    ]
    for r, row in enumerate(matrix):
        for c, dark in enumerate(row):
            if dark:
                parts.append(
                    f'<rect x="{c + 1}" y="{r + 1}" width="1" height="1" fill="#1c2333"/>'
                )
    parts.append("</svg>")
    return "".join(parts)


@app.post("/api/calculate", response_model=CalculateResponse)
def calculate(req: CalculateRequest, db: Session = Depends(get_db)):
    expr = req.expression.strip()
    try:
        value = evaluate(expr)
    except ExpressionError as e:
        raise HTTPException(status_code=422, detail=str(e))

    result = format_result(value)

    record_id = None
    created_at = None
    if req.save:
        record = CalculationHistory(expression=expr, result=result, created_at=utc_now())
        db.add(record)
        try:
            db.commit()
            db.refresh(record)
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(status_code=500, detail="保存历史记录失败")
        record_id = record.id
        created_at = serialize_dt(record.created_at)

    return CalculateResponse(
        expression=expr,
        result=result,
        record_id=record_id,
        created_at=created_at,
    )


@app.get("/api/history", response_model=HistoryResponse)
def history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    db: Session = Depends(get_db),
):
    filters = []
    keyword = search.strip()
    if keyword:
        filters.append(CalculationHistory.expression.contains(keyword))

    total = db.scalar(select(func.count(CalculationHistory.id)).where(*filters)) or 0

    rows = db.scalars(
        select(CalculationHistory)
        .where(*filters)
        .order_by(CalculationHistory.created_at.desc(), CalculationHistory.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    items = [
        HistoryItem(
            id=r.id,
            expression=r.expression,
            result=r.result,
            created_at=serialize_dt(r.created_at),
        )
        for r in rows
    ]
    return HistoryResponse(items=items, total=total, page=page, page_size=page_size)


@app.delete("/api/history", status_code=status.HTTP_204_NO_CONTENT)
def clear_history(db: Session = Depends(get_db)):
    db.execute(delete(CalculationHistory))
    db.commit()


@app.delete("/api/history/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_history(record_id: int, db: Session = Depends(get_db)):
    record = db.get(CalculationHistory, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()


@app.get("/", include_in_schema=False)
def index(request: Request):
    expr = request.query_params.get("expr")
    if not expr:
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    # 服务端预计算并注入初始值，便于演示/截图（无需等待前端异步请求）
    try:
        result = format_result(evaluate(expr))
    except ExpressionError as e:
        result = f"错误：{e}"

    mode = "sci" if request.query_params.get("mode") == "sci" else "basic"
    initial = json.dumps({"expr": expr, "result": result, "mode": mode}, ensure_ascii=False)

    # 渲染最近历史记录
    db = SessionLocal()
    try:
        rows = db.scalars(
            select(CalculationHistory)
            .order_by(CalculationHistory.created_at.desc(), CalculationHistory.id.desc())
            .limit(10)
        ).all()
        hist = "".join(
            f'<li class="history-item" data-expr="{html.escape(r.expression)}">'
            '<div class="hist-body">'
            f'<div class="hist-expr">{html.escape(r.expression)}</div>'
            f'<div class="hist-res">= {html.escape(r.result)}</div>'
            f'<div class="hist-time">{r.created_at.strftime("%Y-%m-%d %H:%M")}</div>'
            "</div>"
            f'<button class="del" data-id="{r.id}" title="删除">×</button>'
            "</li>"
            for r in rows
        )
    finally:
        db.close()

    with open(os.path.join(FRONTEND_DIR, "index.html"), encoding="utf-8") as f:
        content = f.read()
    content = content.replace("</head>", f"<script>window.__INITIAL__ = {initial};</script></head>", 1)
    content = content.replace(
        '<div id="expression" class="expression"></div>',
        f'<div id="expression" class="expression">{html.escape(expr)} =</div>',
        1,
    )
    content = content.replace(
        '<div id="result" class="result">0</div>',
        f'<div id="result" class="result">{html.escape(result)}</div>',
        1,
    )
    content = content.replace(
        '<ul id="history-list" class="history-list"></ul>',
        f'<ul id="history-list" class="history-list">{hist}</ul>',
        1,
    )
    return Response(content, media_type="text/html")


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


if __name__ == "__main__":
    import threading
    import webbrowser

    print("=" * 52)
    print("  计算器已启动")
    print("  本机访问: http://127.0.0.1:8000/")
    print(f"  手机访问: {LAN_URL}  (需与电脑同一 WiFi)")
    print("  页面顶部有二维码，手机扫码即可打开")
    print("  按 Ctrl+C 停止")
    print("=" * 52)

    def _open_browser():
        import time

        time.sleep(1.2)
        webbrowser.open("http://127.0.0.1:8000/")

    threading.Thread(target=_open_browser, daemon=True).start()

    import uvicorn

    # 绑定 0.0.0.0 以允许同一局域网内的手机访问
    uvicorn.run(app, host="0.0.0.0", port=8000)
