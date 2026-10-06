# 前后端分离计算器

## 课程信息说明（Course Information）

| 项目 | 内容 |
|---|---|
| Course for This Assignment（本作业所属课程） | 【请填写课程名称，如：软件工程实践】 |
| Assignment Requirements（作业要求） | 完成一个前后端分离的计算器：前端负责界面与交互，后端负责安全表达式求值、高精度计算与历史记录存储，前后端通过 REST API 交互，并按要求提交博客与 GitHub 仓库 |
| Objectives of This Assignment（本作业目标） | 掌握前后端分离开发、REST API 设计、安全的表达式求值、数据库的使用，以及 Git/GitHub 协作与 PSP 流程 |
| Other References（参考资料） | FastAPI 官方文档、SQLAlchemy 官方文档、CSDN 相关博客、【可继续补充】 |

## 目录（Table of Contents）

> 若发布在 CSDN，可将本段替换为 `@[TOC]` 自动生成目录，保证能正确跳转。

- [Git 仓库链接与代码规范链接](#git-仓库链接与代码规范链接)
- [PSP 表](#psp-表)
- [成品展示](#成品展示)
- [设计与实现过程](#设计与实现过程)
- [代码说明](#代码说明)
- [测试报告](#测试报告)
- [个人心得与总结](#个人心得与总结)

---

## Git 仓库链接与代码规范链接

- **Git 仓库链接**：<https://github.com/zhangjt123/calculator>
- **代码规范链接**：【请填写课程代码规范文档链接，如班级统一的编码规范】

> 仓库结构：`backend/`（FastAPI 后端）、`frontend/`（HTML/CSS/JS 前端）、`docs/`（本博客与截图）、`start.bat`（一键启动脚本）。

---

## PSP 表

| PSP2.1 | Personal Software Process Stages | 预估耗时（分钟） | 实际耗时（分钟） |
|---|---|---|---|
| Planning | 计划 | | |
| · Estimate | · 估计这个任务需要多少时间 | | |
| Development | 开发 | | |
| · Analysis | · 需求分析（包括学习新技术） | | |
| · Design Spec | · 生成设计文档 | | |
| · Design Review | · 设计复审 | | |
| · Coding Standard | · 代码规范（为目前的开发制定合适的规范） | | |
| · Design | · 具体设计 | | |
| · Coding | · 具体编码 | | |
| · Code Review | · 代码复审 | | |
| · Test | · 测试（自我测试，修改代码，提交修改） | | |
| Reporting | 报告 | | |
| · Test Report | · 测试报告 | | |
| · Size Measurement | · 计算工作量 | | |
| · Postmortem & Process Improvement Plan | · 事后总结，并提出过程改进计划 | | |
| **合计** | | | |

---

## 成品展示

### 项目访问链接

| 类型 | 地址 |
|---|---|
| 本地运行 | <http://127.0.0.1:8000/> |
| 公网部署 | 【待部署后填写】 |

**可直接访问的计算示例链接**（后端运行时生效，打开即显示已算好的结果，无需手动输入）：

- 高精度示例：<http://127.0.0.1:8000/?expr=0.1%2B0.2> → `0.1+0.2 = 0.3`
- 科学计算示例：<http://127.0.0.1:8000/?expr=sin%2830%29%2Bsqrt%2816%29&mode=sci> → `sin(30)+sqrt(16) = 4.5`

### 运行方式

双击 `start.bat`（首次自动创建虚拟环境、安装依赖、启动服务并自动打开浏览器），或手动：

```powershell
cd calculator
.\.venv\Scripts\python.exe backend\main.py
```

### 界面截屏

**基础模式（高精度：0.1 + 0.2 = 0.3）**

![基础模式计算示例](screenshots/1-basic.png)

**科学模式（sin(30) + sqrt(16) = 4.5）**

![科学模式计算示例](screenshots/2-scientific.png)

**手机端界面**

![手机端界面](screenshots/3-mobile.png)

### 功能特性

- **基础模式**：四则运算、括号、小数、`±` 正负、`%` 百分号、退格/清除
- **科学模式**（右上角「科学」按钮展开）：`√` 开平方、`x²` 平方、`xʸ` 幂、`1/x` 倒数、`n!` 阶乘、`π`/`e` 常量、`sin/cos/tan/asin/atan`、`ln/log`
- **实时预览**：输入即出结果，按 `=` 才写入历史
- **高精度**：`0.1 + 0.2 = 0.3`、`√2` 50 位有效数字
- **历史记录**：搜索、分页、点击回填、删除、一键清空、复制结果
- **键盘输入**：Enter 计算 / Esc 清空 / ⌫ 退格 / % 百分号 / ^ 幂
- **手机适配**：响应式布局、大触控按钮、页面顶部二维码扫码即开

---

## 设计与实现过程

### 1. 整体架构

```
┌─────────────────┐   HTTP(REST API)   ┌──────────────────┐   SQLAlchemy   ┌──────────────────┐
│  前端 frontend/  │ ─────────────────▶ │   后端 backend/   │ ─────────────▶ │     数据库        │
│  HTML/CSS/JS    │ ◀───────────────── │     FastAPI       │ ◀───────────── │ calculation_history│
│  (界面与交互)     │        JSON         │  (求值/存储/API)   │                │  (SQLite/PostgreSQL)│
└─────────────────┘                     └──────────────────┘                └──────────────────┘
```

前后端彻底分离：前端只负责「收集表达式 → 调用 API → 展示结果与历史」，计算逻辑、安全校验、数据持久化全部在后端完成。

### 2. 技术栈与选型理由

| 层 | 技术 | 理由 |
|---|---|---|
| 后端 | FastAPI + SQLAlchemy 2.0 | 原生异步、自动生成 `/docs` 文档、类型校验（Pydantic） |
| 数据库 | SQLite（本地）/ Neon PostgreSQL（生产） | 本地零配置，生产可无缝切换 |
| 前端 | 原生 HTML/CSS/JS（fetch） | 无构建依赖，轻量、易部署 |

### 3. 后端模块划分

| 文件 | 职责 |
|---|---|
| `evaluator.py` | 安全表达式求值器（AST 白名单 + Decimal 高精度） |
| `db.py` | 数据库连接、`calculation_history` 表模型 |
| `main.py` | FastAPI 应用、REST API、前端静态托管、二维码接口 |

### 4. 安全求值设计（核心难点）

**为什么不能直接用 `eval()`？** `eval()` 会执行任意 Python 代码，例如 `__import__('os').system('...')`，存在严重安全隐患。本作业采用 **AST 白名单** 方案：

1. **字符白名单**：只允许 `数字 0-9、小数点、+ - * /、括号、空白、字母`（字母仅用于函数名与常量 `pi`/`e`）；
2. **长度限制**：表达式 ≤ 200 字符；
3. **AST 解析**：`ast.parse(expr, mode="eval")` 解析成语法树；
4. **节点白名单**：递归校验只放行 `Expression / BinOp / UnaryOp / Constant / Name(pi,e) / Call(白名单函数)`；
5. **深度限制**：AST 嵌套 ≤ 32 层，防止深层嵌套攻击；
6. **函数白名单**：仅 `sqrt/sin/cos/tan/asin/acos/atan/ln/log/exp/factorial/abs`，且必须是一元调用。

于是 `__import__('os')`、`2**3`（未开放前）、`sin(1)`（未开放前）、任意变量名都会被拒绝。

### 5. 高精度设计

二进制浮点数无法精确表示 0.1、0.2，导致 `0.1 + 0.2 = 0.30000000000000004`。本作业用 `decimal.Decimal`（50 位有效数字、half-even 舍入），并且**从源码原文读取数字字面量**而非已损失的 float：

```python
if isinstance(node, ast.Constant):
    literal = ast.get_source_segment(source, node)  # 原始字面量，如 "0.1"
    return Decimal(literal)                          # Decimal("0.1")，精确
```

最终 `0.1 + 0.2` 精确返回 `0.3`。三角/对数等超越函数用 `math` 浮点实现（约 15 位有效数字），三角函数按角度制。

### 6. 数据库设计

表 `calculation_history`：

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER 主键自增 | 用于检索/删除 |
| expression | VARCHAR(200) | 规范化后的表达式 |
| result | VARCHAR(1024) | 十进制结果 |
| created_at | DATETIME | 时间戳（UTC，前端转本地显示） |

- `(created_at, id)` 联合索引，保证稳定的倒序排序；
- **失败的表达式不写入历史**（先求值成功再入库）；
- 本地 SQLite、生产 Neon PostgreSQL，通过 `DATABASE_URL` 环境变量切换。

### 7. API 设计

| 方法 | 端点 | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查，返回 `{"status":"ok"}` |
| POST | `/api/calculate` | 计算表达式，请求体 `{"expression":"0.1+0.2","save":true}` |
| GET | `/api/history?page=1&page_size=20&search=` | 分页/搜索历史记录 |
| DELETE | `/api/history` | 清空全部历史 |
| DELETE | `/api/history/{record_id}` | 删除指定记录（204；不存在 404） |
| GET | `/api/info` | 返回局域网访问地址 |
| GET | `/api/qr` | 返回手机访问地址二维码（SVG） |

### 8. 前后端交互流程

```
用户输入表达式 → 前端 debounce 250ms → POST /api/calculate (save=false) → 后端求值 → 前端实时预览
用户按 "="     → POST /api/calculate (save=true)  → 后端求值 + 写入历史 → 前端显示结果 + 刷新历史
```

---

## 代码说明

### 1. 安全求值器 `backend/evaluator.py`

白名单校验是安全的核心：

```python
_ALLOWED_BIN_OPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)
_ALLOWED_UNARY_OPS = (ast.UAdd, ast.USub)
_ALLOWED_FUNCS = frozenset({
    "sqrt", "sin", "cos", "tan", "asin", "acos", "atan",
    "ln", "log", "exp", "factorial", "abs",
})
_CONSTANTS = {
    "pi": Decimal("3.1415926535897932384626433832795028841971693993751"),
    "e":  Decimal("2.7182818284590452353602874713526624977572470937"),
}

def _validate_tree(node, source, depth=0):
    if depth > MAX_DEPTH:  # 32
        raise ExpressionError("表达式嵌套层级不能超过 32")
    if isinstance(node, ast.BinOp):
        if type(node.op) not in _ALLOWED_BIN_OPS:
            raise ExpressionError("不支持的二元运算符")
        _validate_tree(node.left, source, depth + 1)
        _validate_tree(node.right, source, depth + 1)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ExpressionError("仅支持数字常量")
    elif isinstance(node, ast.Call):
        # 只放行白名单函数、且只有一个参数、无关键字参数
        if (isinstance(node.func, ast.Name)
                and node.func.id in _ALLOWED_FUNCS
                and len(node.args) == 1 and not node.keywords):
            _validate_tree(node.args[0], source, depth + 1)
        else:
            raise ExpressionError("不支持的函数调用")
    else:
        raise ExpressionError(f"不支持的元素：{type(node).__name__}")
```

幂运算做了防滥用限制：

```python
if isinstance(node.op, ast.Pow):
    if abs(right) > 1000:
        raise ExpressionError("指数过大")
    if abs(left) > 10**9:
        raise ExpressionError("底数过大")
    return left ** right
```

### 2. 后端 API `backend/main.py`

```python
@app.post("/api/calculate", response_model=CalculateResponse)
def calculate(req: CalculateRequest, db: Session = Depends(get_db)):
    expr = req.expression.strip()
    try:
        value = evaluate(expr)               # 安全求值
    except ExpressionError as e:
        raise HTTPException(status_code=422, detail=str(e))

    result = format_result(value)            # 去尾零/负零

    if req.save:                             # 仅 save=true 写入历史
        record = CalculationHistory(expression=expr, result=result, created_at=utc_now())
        db.add(record); db.commit(); db.refresh(record)
        return CalculateResponse(expression=expr, result=result,
                                 record_id=record.id, created_at=serialize_dt(record.created_at))
    return CalculateResponse(expression=expr, result=result, record_id=None, created_at=None)
```

### 3. 前端交互 `frontend/app.js`

实时预览通过 `debounce` 防抖 + `save=false` 实现，避免每敲一个字符就写一条历史：

```javascript
const preview = debounce(async () => {
  const data = await api("/api/calculate", {
    method: "POST",
    body: JSON.stringify({ expression: currentExpression, save: false }), // 预览不落库
  });
  resultEl.textContent = data.result;   // 实时显示结果
}, 250);
```

---

## 测试报告

### 功能测试

| 表达式 | 预期 | 实际结果 | 结论 |
|---|---|---|---|
| `0.1+0.2` | `0.3` | `0.3` | ✅ |
| `2*(3+4)/5` | `2.8` | `2.8` | ✅ |
| `sqrt(16)` | `4` | `4` | ✅ |
| `sqrt(2)` | 50 位精度 | `1.4142135623730950488016887242096980785696718753769` | ✅ |
| `sin(30)` | `0.5` | `0.5` | ✅ |
| `cos(60)` | `0.5` | `0.5` | ✅ |
| `tan(45)` | `1` | `1` | ✅ |
| `asin(0.5)` | `30` | `30` | ✅ |
| `ln(e)` / `log(100)` | `1` / `2` | `1` / `2` | ✅ |
| `factorial(5)` | `120` | `120` | ✅ |
| `2**10` | `1024` | `1024` | ✅ |
| `2*pi` | `6.283…` | `6.2831853071795864769252867665590057683943387987502` | ✅ |

### 安全与异常测试

| 输入 | 预期 | 实际结果 | 结论 |
|---|---|---|---|
| `__import__('os')` | 拒绝 | 包含非法字符：`_` | ✅ |
| `sin(1)`（未开放函数） | 拒绝 | 不支持的函数调用 | ✅ |
| `1/0` | 报错 | 除数不能为零 | ✅ |
| `ln(-1)` | 报错 | 函数定义域错误 | ✅ |
| `factorial(1.5)` | 报错 | 阶乘仅支持非负整数 | ✅ |
| `9**999999` | 报错 | 指数过大 | ✅ |
| 超 200 字符表达式 | 报错 | 表达式长度不能超过 200 | ✅ |
| 超 32 层嵌套 | 报错 | 表达式嵌套层级不能超过 32 | ✅ |

---

## 个人心得与总结

（以下为草稿，请结合个人实际体验修改）

1. **对前后端分离的理解**：本次作业让我真正体会到「前端管界面、后端管逻辑」的分工——前端只负责把表达式发给后端、把结果和历史上屏，计算与存储全部由后端完成，职责清晰、便于扩展。

2. **安全求值的重要性**：一开始最容易想到 `eval()`，但它能执行任意代码，风险极大。改用 AST 白名单后，才明白「安全」不是加一层密码，而是从源头限定「允许什么」。

3. **浮点精度的坑**：`0.1 + 0.2 != 0.3` 是浮点数表示带来的经典问题。通过 `Decimal` + 从源码原文读字面量，真正做到了精确计算。

4. **遇到的最大困难与解决**：实时预览会污染历史记录（每输入一个字符就存一条）。通过给 `/api/calculate` 增加 `save` 参数、预览时 `save=false` 解决。

5. **改进方向**：后续可增加 DEG/RAD 角度切换、双曲函数、内存功能（MC/MR/M+），以及完善的单元测试。

---

## 提交说明（Submission Rules）

- 提交时间以班级作业页为准，代码提交以 GitHub 为准。
- 逾期 2 天内按实际分数 50% 计；超过 2 天未交计 0 分。
- 抄袭（两篇博客文字/图片/代码过于相似）双方均计 -100%。
- 提前占位但未完成视为伪造提交，计 0 分。
