# 前后端分离计算器

基于 FastAPI + 原生 HTML/CSS/JS 的前后端分离计算器。浅色主题，内置**基础 / 科学双模式**，支持手机浏览器访问（页面顶部有二维码，扫码即开）。

## 项目结构

```
calculator/
├── start.bat              # 双击启动（自动装依赖、启动服务、打开浏览器）
├── backend/
│   ├── main.py            # FastAPI 应用（API + 前端静态托管 + 二维码接口）
│   ├── evaluator.py       # 安全高精度表达式求值器
│   ├── db.py              # SQLAlchemy 数据层（SQLite / PostgreSQL）
│   └── requirements.txt
├── frontend/
│   ├── index.html         # 计算器界面（浅色、响应式、双模式）
│   ├── style.css
│   └── app.js             # 通过 fetch 调用后端 API
└── README.md
```

## 快速启动

双击 `start.bat`：首次运行自动创建虚拟环境并安装依赖，随后启动后端、自动打开浏览器。

- 本机访问：<http://127.0.0.1:8000/>
- 手机访问：页面顶部二维码扫码，或控制台打印的 `http://<本机IP>:8000/`（同一 WiFi）
- API 文档：<http://127.0.0.1:8000/docs>

> 若手机无法访问，请在 Windows 防火墙中允许 Python 通过。

## 功能特性

- **基础模式**：四则运算、括号、小数、`±` 正负、`%` 百分号、退格/清除
- **科学模式**（点右上角「科学」展开）：`√` 开平方、`x²` 平方、`xʸ` 幂、`1/x` 倒数、`n!` 阶乘、`π`/`e` 常量、`sin/cos/tan/asin/atan`、`ln/log`
- **实时预览**：输入即出结果，按 `=` 才写入历史
- **高精度**：`0.1 + 0.2 = 0.3`、`√2` 50 位有效数字（三角/对数用浮点，约 15 位）
- **历史记录**：搜索、分页、点击回填、删除、一键清空、一键复制结果
- **键盘输入**：Enter 计算 / Esc 清空 / ⌫ 退格 / % 百分号 / ^ 幂
- **手机适配**：响应式单列、大触控按钮；三角函数按角度制

## API 说明

| 方法 | 端点 | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查，返回 `{"status":"ok"}` |
| POST | `/api/calculate` | 计算表达式，请求体 `{"expression":"sin(30)+sqrt(16)","save":true}` |
| GET | `/api/history?page=1&page_size=20&search=` | 分页/搜索历史记录 |
| DELETE | `/api/history` | 清空全部历史 |
| DELETE | `/api/history/{record_id}` | 删除指定记录（成功 204，不存在 404） |
| GET | `/api/info` | 返回局域网访问地址 |
| GET | `/api/qr` | 返回手机访问地址的二维码（SVG） |

## 安全与精度设计

- **AST 白名单**：仅放行 `Expression / BinOp / UnaryOp / Constant / Name(pi,e) / Call(白名单函数)`，拒绝任意函数调用、变量名、属性访问等。
- **函数白名单**：仅 `sqrt sin cos tan asin acos atan ln log exp factorial abs`，且必须是一元调用。
- **常量白名单**：仅 `pi`、`e`。
- **字符白名单**：仅允许数字、小数点、运算符、括号、空白和字母（字母仅用于函数名/常量）。
- **长度/深度限制**：表达式 ≤ 200 字符，AST 嵌套 ≤ 32 层。
- **幂运算限制**：指数 ≤ 1000、底数 ≤ 10⁹，防止超大幂拖垮服务。
- **高精度 Decimal**：从源码原文读取数字字面量、50 位有效数字、half-even 舍入。
- **历史记录**：失败的表达式不写入数据库；`(created_at, id)` 联合索引保证稳定倒序。

## 切换 PostgreSQL（生产环境）

设置 `DATABASE_URL` 环境变量并安装 `psycopg2-binary` 即可，代码无需改动：

```powershell
$env:DATABASE_URL = "postgresql+psycopg2://user:password@host:5432/dbname"
```
