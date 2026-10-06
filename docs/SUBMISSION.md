# Front-End and Back-End Separation Calculator System

## Course Information

| Item | Content |
|---|---|
| Name | Jingtian Zhang |
| FZU STU ID | 832401323 |
| MU STU ID | 24125270 |
| Course for This Assignment | EE308FZ — Software Engineering |
| Assignment | First Assignment — Front-End and Back-End Separation Calculator System |
| Assignment Requirements | Build a front-end and back-end separated calculator: the frontend handles the UI and interaction, while the backend handles secure expression evaluation, high-precision computation, and history storage. The two parts communicate through REST API. |
| Objectives of This Assignment | Master front-end/back-end separation, REST API design, secure expression evaluation, database usage, and Git/GitHub collaboration. |
| Other References | [FastAPI documentation](https://fastapi.tiangolo.com/), [SQLAlchemy documentation](https://www.sqlalchemy.org/), [Python `decimal` module](https://docs.python.org/3/library/decimal.html) |

## Table of Contents

- [Git Repository Link and Code Standards Link](#git-repository-link-and-code-standards-link)
- [PSP Table](#psp-table)
- [Presentation of the Finished Product](#presentation-of-the-finished-product)
- [Design and Implementation Process](#design-and-implementation-process)
- [Code Explanation](#code-explanation)
- [Test Report](#test-report)
- [Personal Journey and Learnings](#personal-journey-and-learnings)

---

## Git Repository Link and Code Standards Link

- **Git Repository Link**: <https://github.com/zhangjt123/calculator>
- **Code Standards Link**: [to be filled — course coding standard document]

> Repository structure: `backend/` (FastAPI backend), `frontend/` (HTML/CSS/JS frontend), `docs/` (this blog and screenshots), `start.bat` (one-click launcher).

---

## PSP Table

| PSP2.1 | Personal Software Process Stages | Estimated Time (min) | Actual Time (min) |
|---|---|---|---|
| Planning | Plan | | |
| · Estimate | · Estimate how much time this task needs | | |
| Development | Development | | |
| · Analysis | · Requirements analysis (including learning new technology) | | |
| · Design Spec | · Generate design documents | | |
| · Design Review | · Design review | | |
| · Coding Standard | · Code specification (develop suitable specifications for the current development) | | |
| · Design | · Specific design | | |
| · Coding | · Specific coding | | |
| · Code Review | · Code review | | |
| · Test | · Test (self-test, modify code, submit modifications) | | |
| Reporting | Report | | |
| · Test Report | · Test report | | |
| · Size Measurement | · Calculate workload | | |
| · Postmortem & Process Improvement Plan | · Summarize afterwards and propose process improvement plan | | |
| **Total** | | | |

---

## Presentation of the Finished Product

### Project Access Links

| Type | URL |
|---|---|
| Local run | <http://127.0.0.1:8000/> |
| Public deployment | [to be filled after deployment] |

**Directly accessible calculation example links** (work when the backend is running; the result is shown immediately after the page loads):

- High-precision example: <http://127.0.0.1:8000/?expr=0.1%2B0.2> → `0.1+0.2 = 0.3`
- Scientific example: <http://127.0.0.1:8000/?expr=sin%2830%29%2Bsqrt%2816%29&mode=sci> → `sin(30)+sqrt(16) = 4.5`

### How to Run

Double-click `start.bat` (it creates the virtual environment, installs dependencies, starts the server, and opens the browser on the first run), or manually:

```powershell
cd calculator
.\.venv\Scripts\python.exe backend\main.py
```

### Screenshots

**Basic mode (high precision: 0.1 + 0.2 = 0.3)**

![Basic mode calculation example](screenshots/1-basic.png)

**Scientific mode (sin(30) + sqrt(16) = 4.5)**

![Scientific mode calculation example](screenshots/2-scientific.png)

**Mobile view**

![Mobile view](screenshots/3-mobile.png)

### Features

- **Basic mode**: four arithmetic operations, parentheses, decimals, `±` sign toggle, `%` percent, backspace/clear
- **Scientific mode** (toggle via the "科学" button): `√` square root, `x²` square, `xʸ` power, `1/x` reciprocal, `n!` factorial, `π`/`e` constants, `sin/cos/tan/asin/atan`, `ln/log`
- **Live preview**: the result appears as you type; pressing `=` writes it to history
- **High precision**: `0.1 + 0.2 = 0.3`, `√2` with 50 significant digits
- **History**: search, pagination, click-to-refill, delete, clear all, copy result
- **Keyboard input**: Enter = calculate, Esc = clear, Backspace = delete, `%` = percent, `^` = power
- **Mobile friendly**: responsive layout, large touch targets, QR code at the top for instant access

---

## Design and Implementation Process

### 1. Overall Architecture

```
┌──────────────────┐   HTTP (REST API)   ┌───────────────────┐   SQLAlchemy   ┌────────────────────┐
│  frontend/        │ ──────────────────▶ │  backend/          │ ─────────────▶ │  Database          │
│  HTML/CSS/JS      │ ◀────────────────── │  FastAPI           │ ◀───────────── │  calculation_history│
│  (UI & interaction)│        JSON         │  (evaluation/API)  │                │  (SQLite/PostgreSQL)│
└──────────────────┘                     └───────────────────┘                └────────────────────┘
```

The frontend and backend are fully separated: the frontend only collects the expression, calls the API, and displays the result and history; all computation, security checks, and persistence happen in the backend.

### 2. Technology Stack and Rationale

| Layer | Technology | Rationale |
|---|---|---|
| Backend | FastAPI + SQLAlchemy 2.0 | Native async, automatic `/docs`, Pydantic validation |
| Database | SQLite (local) / Neon PostgreSQL (production) | Zero-config locally; seamless switch in production |
| Frontend | Vanilla HTML/CSS/JS (fetch) | No build step, lightweight, easy to deploy |

### 3. Backend Modules

| File | Responsibility |
|---|---|
| `evaluator.py` | Secure expression evaluator (AST whitelist + Decimal high precision) |
| `db.py` | Database connection and the `calculation_history` model |
| `main.py` | FastAPI app, REST API, static hosting, QR-code endpoint |

### 4. Secure Evaluation (the key difficulty)

**Why not just `eval()`?** `eval()` executes arbitrary Python code, e.g. `__import__('os').system('...')`, which is a serious security risk. This assignment uses an **AST whitelist** approach:

1. **Character whitelist**: only `digits 0-9, decimal point, + - * /, parentheses, whitespace, letters` (letters are only for function names and the constants `pi`/`e`);
2. **Length limit**: expression ≤ 200 characters;
3. **AST parsing**: `ast.parse(expr, mode="eval")`;
4. **Node whitelist**: recursively allow only `Expression / BinOp / UnaryOp / Constant / Name(pi,e) / Call(whitelisted functions)`;
5. **Depth limit**: AST nesting ≤ 32 levels to prevent deep-nesting attacks;
6. **Function whitelist**: only `sqrt/sin/cos/tan/asin/acos/atan/ln/log/exp/factorial/abs`, and only as unary calls.

As a result, `__import__('os')`, arbitrary names, and unapproved function calls are all rejected.

### 5. High-Precision Computation

Binary floating-point cannot represent 0.1 and 0.2 exactly, so `0.1 + 0.2` yields `0.30000000000000004`. This assignment uses `decimal.Decimal` (50 significant digits, half-even rounding) and reads number literals **from the source text** instead of the lossy float:

```python
if isinstance(node, ast.Constant):
    literal = ast.get_source_segment(source, node)  # original literal, e.g. "0.1"
    return Decimal(literal)                          # Decimal("0.1"), exact
```

Thus `0.1 + 0.2` returns exactly `0.3`. Transcendental functions (trig/log) use `math` floating point (~15 significant digits); trigonometric functions are in degrees.

### 6. Database Design

Table `calculation_history`:

| Field | Type | Description |
|---|---|---|
| id | INTEGER primary key, auto-increment | used for retrieval/deletion |
| expression | VARCHAR(200) | normalized expression |
| result | VARCHAR(1024) | decimal result |
| created_at | DATETIME | timestamp (UTC, converted to local time on the frontend) |

- `(created_at, id)` composite index for stable descending order;
- **Failed expressions are never written** (evaluation succeeds before insertion);
- Local SQLite; production Neon PostgreSQL via the `DATABASE_URL` environment variable.

### 7. API Design

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check, returns `{"status":"ok"}` |
| POST | `/api/calculate` | Evaluate expression, body `{"expression":"0.1+0.2","save":true}` |
| GET | `/api/history?page=1&page_size=20&search=` | Paginated / searchable history |
| DELETE | `/api/history` | Clear all history |
| DELETE | `/api/history/{record_id}` | Delete one record (204; 404 if missing) |
| GET | `/api/info` | Return the LAN access URL |
| GET | `/api/qr` | Return a QR code (SVG) of the LAN URL |

### 8. Frontend-Backend Interaction

```
User types → frontend debounce 250 ms → POST /api/calculate (save=false) → evaluate → live preview
User presses "=" → POST /api/calculate (save=true) → evaluate + save history → show result + refresh history
```

---

## Code Explanation

### 1. Secure evaluator `backend/evaluator.py`

Whitelist validation is the core of the security:

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
        raise ExpressionError("expression nesting exceeds 32 levels")
    if isinstance(node, ast.BinOp):
        if type(node.op) not in _ALLOWED_BIN_OPS:
            raise ExpressionError("unsupported binary operator")
        _validate_tree(node.left, source, depth + 1)
        _validate_tree(node.right, source, depth + 1)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ExpressionError("only numeric constants are allowed")
    elif isinstance(node, ast.Call):
        # allow only whitelisted functions with exactly one positional argument
        if (isinstance(node.func, ast.Name)
                and node.func.id in _ALLOWED_FUNCS
                and len(node.args) == 1 and not node.keywords):
            _validate_tree(node.args[0], source, depth + 1)
        else:
            raise ExpressionError("unsupported function call")
    else:
        raise ExpressionError(f"unsupported element: {type(node).__name__}")
```

Power operations are bounded to prevent abuse:

```python
if isinstance(node.op, ast.Pow):
    if abs(right) > 1000:
        raise ExpressionError("exponent too large")
    if abs(left) > 10**9:
        raise ExpressionError("base too large")
    return left ** right
```

### 2. Backend API `backend/main.py`

```python
@app.post("/api/calculate", response_model=CalculateResponse)
def calculate(req: CalculateRequest, db: Session = Depends(get_db)):
    expr = req.expression.strip()
    try:
        value = evaluate(expr)                # secure evaluation
    except ExpressionError as e:
        raise HTTPException(status_code=422, detail=str(e))

    result = format_result(value)             # strip trailing zeros / negative zero

    if req.save:                              # write to history only when save=True
        record = CalculationHistory(expression=expr, result=result, created_at=utc_now())
        db.add(record); db.commit(); db.refresh(record)
        return CalculateResponse(expression=expr, result=result,
                                 record_id=record.id, created_at=serialize_dt(record.created_at))
    return CalculateResponse(expression=expr, result=result, record_id=None, created_at=None)
```

### 3. Frontend interaction `frontend/app.js`

Live preview uses `debounce` plus `save=false` to avoid writing one history record per keystroke:

```javascript
const preview = debounce(async () => {
  const data = await api("/api/calculate", {
    method: "POST",
    body: JSON.stringify({ expression: currentExpression, save: false }), // preview, not saved
  });
  resultEl.textContent = data.result;   // show the result live
}, 250);
```

---

## Test Report

### Functional Tests

| Expression | Expected | Actual | Result |
|---|---|---|---|
| `0.1+0.2` | `0.3` | `0.3` | ✅ |
| `2*(3+4)/5` | `2.8` | `2.8` | ✅ |
| `sqrt(16)` | `4` | `4` | ✅ |
| `sqrt(2)` | 50-digit precision | `1.4142135623730950488016887242096980785696718753769` | ✅ |
| `sin(30)` | `0.5` | `0.5` | ✅ |
| `cos(60)` | `0.5` | `0.5` | ✅ |
| `tan(45)` | `1` | `1` | ✅ |
| `asin(0.5)` | `30` | `30` | ✅ |
| `ln(e)` / `log(100)` | `1` / `2` | `1` / `2` | ✅ |
| `factorial(5)` | `120` | `120` | ✅ |
| `2**10` | `1024` | `1024` | ✅ |
| `2*pi` | `6.283…` | `6.2831853071795864769252867665590057683943387987502` | ✅ |

### Security & Exception Tests

| Input | Expected | Actual | Result |
|---|---|---|---|
| `__import__('os')` | rejected | illegal character `_` | ✅ |
| unapproved function call | rejected | unsupported function call | ✅ |
| `1/0` | error | division by zero | ✅ |
| `ln(-1)` | error | domain error | ✅ |
| `factorial(1.5)` | error | factorial requires a non-negative integer | ✅ |
| `9**999999` | error | exponent too large | ✅ |
| >200-character expression | error | expression exceeds 200 characters | ✅ |
| >32-level nesting | error | expression nesting exceeds 32 levels | ✅ |

---

## Personal Journey and Learnings

(Draft — please personalize based on your actual experience.)

1. **Understanding front-end/back-end separation**: This assignment made me truly appreciate the division of labor — the frontend only sends the expression and renders results/history, while computation and storage stay in the backend. Responsibilities are clear and easy to extend.

2. **The importance of secure evaluation**: The first instinct is `eval()`, but it can execute arbitrary code. Switching to an AST whitelist taught me that security is not an extra layer, but a decision about what to *allow* from the very start.

3. **The floating-point pitfall**: `0.1 + 0.2 != 0.3` is a classic problem of binary floating-point representation. Using `Decimal` together with reading literals from source text achieved truly exact arithmetic.

4. **Biggest difficulty and its solution**: Live preview would pollute the history (one record per keystroke). I solved it by adding a `save` parameter to `/api/calculate` and using `save=false` during preview.

5. **Future improvements**: DEG/RAD angle switch, hyperbolic functions, memory functions (MC/MR/M+), and a full unit-test suite.

---

## Submission Rules (Reminder)

- The blog deadline follows the class assignment page; the code deadline follows GitHub.
- Submitting within 2 days after the deadline counts as late (50% of the actual score); more than 2 days late counts as missed (0).
- Plagiarism (two blogs too similar in text/images/code) results in -100% for both.
- Early placeholder submissions that are incomplete are treated as falsified submissions (0).
