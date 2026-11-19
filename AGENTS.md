# AGENTS.md - Clean Architecture & Engineering Rules

You are working on a Python 3.12 project strictly following **Clean Architecture** (Feature-sliced within Layers). Any code you generate or modify MUST pass all static analysis, type checking, and architectural gates in CI.

---

## 1. Architectural Layer Boundaries (Strict Dependency Rule)

Dependencies MUST ONLY point inwards:
`src.presentation` -> `src.infrastructure` -> `src.application` -> `src.domain`

### `src/domain/` (Core Business Logic)
- **Allowed:** Pure Python standard library (`dataclasses`, `typing`, `uuid`, `datetime`, `decimal`, `enum`, `re`) and `src.domain.shared`.
- **Forbidden:**
  - NO imports from `application`, `infrastructure`, or `presentation`.
  - NO cross-domain imports (e.g., `src.domain.order` CANNOT import from `src.domain.user`). Put shared concepts in `src.domain.shared`.
  - NO external frameworks or I/O libraries (`fastapi`, `sqlalchemy`, `pydantic`, `httpx`, `aio_pika`, `celery`).
  - NO built-in side-effects (`print()`, `open()`, `eval()`, `exec()`, `importlib`).
  - Entities MUST be pure `@dataclass` classes; NEVER inherit from `BaseModel` or `DeclarativeBase`.

### `src/application/` (Use Cases & Ports)
- **Allowed:** `src.domain` and Python standard library.
- **Forbidden:**
  - NO imports from `infrastructure` or `presentation`.
  - NO external I/O libraries (`fastapi`, `sqlalchemy`, `pydantic`, `httpx`, `aio_pika`, `celery`).
  - NO `print()`, `open()`, or dynamic imports (`importlib`).
- **Mandatory Rules:**
  - Every interface in `ports.py` MUST use `typing.Protocol` and its class name MUST start with **`I`** (e.g., `IUserRepository`, `IOrderEventPublisher`).
  - Every Use Case class MUST end with **`UseCase`** (e.g., `RegisterUserUseCase`) and receive all dependencies via `__init__` using Port interfaces.
  - Every parameter in `UseCase.__init__` MUST have an explicit type annotation; **`Any` is strictly forbidden**.
  - Use Cases MUST NOT call other Use Cases directly. Inject the required `I*Repository` interface instead.
  - External API calls or message publishing (RabbitMQ) MUST execute **outside** the `async with self._uow:` database transaction block.
  - For operational logging inside Use Cases, use Python's standard `logging.getLogger(__name__)` ONLY (never `print()`).

### `src/infrastructure/` (Adapters, Observability & Configuration)
- **Allowed:** Implements interfaces defined in `src.application` using concrete libraries (`SQLAlchemy`, `HTTPX`, `aio-pika`, `pydantic-settings`), plus JSON structured logging and `ContextVar` correlation ID management (`src/infrastructure/observability/`).
- **Rules:**
  - Repositories (`sqlalchemy_*_repo.py`) MUST map between ORM Models and Domain Entities, and call `await session.flush()` instead of `commit()` (transaction commits belong to `UnitOfWork`).
  - Environment variables MUST only be accessed via `AppConfig` (`src/infrastructure/config/app_config.py`). If adding a new env variable, update `AppConfig` and `.env.example` ONLY (never modify `.env`).

### `src/presentation/` (FastAPI Routers, Middlewares, Celery Workers & Composition Root)
- **Allowed:** FastAPI routers (`api/v1/`), HTTP middlewares (`api/middlewares/`), Celery tasks (`workers/`), and Dependency Injection wiring (`dependencies/`).
- **Rules:**
  - FastAPI endpoints and Celery tasks MUST NOT contain business logic or direct database queries. They only parse input DTOs, invoke a `UseCase`, and map domain exceptions to HTTP responses or task outputs.
  - Health check endpoints (`/health/live`, `/health/ready`) MUST remain lightweight and free of domain business logic.

---

## 2. Coding Standards & Type Safety (Mypy Strict Mode)
- **Line length:** Maximum `100` characters.
- **Function complexity:** McCabe complexity (`C901`) MUST NOT exceed `10`. Break large functions into small, focused helper methods.
- **Strict Type Safety (`mypy --strict`):**
  - All function parameters, return types, class attributes, and generic collections (e.g., `list[str]`, `dict[str, object]`) MUST be explicitly typed across `src/`.
  - `Any` is forbidden in domain/application code and discouraged everywhere else.
  - Never add blanket `# type: ignore` comments; fix the underlying type mismatch or handle `None` explicitly.

---

## 3. Mandatory Pre-Completion Verification
Before finishing any task or submitting code, you MUST run and pass all five commands below with zero errors:

```bash
ruff format --check src tests alembic
ruff check src tests alembic
lint-imports
python -m mypy src
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## 4. Database & Alembic Migration Rules
- **Model Registration:** Whenever you create or modify an ORM model, ensure it is imported in `src/infrastructure/database/models.py` (which exposes `Base.metadata` to `alembic/env.py`).
- **Mandatory Migration Generation:** You MUST NEVER modify SQLAlchemy ORM models without generating a corresponding migration file via:
  `alembic revision --autogenerate -m "<concise_description>"`
- **No Hand-Written Raw DDL:** Do not alter database schemas manually; always use Alembic migrations and verify that `alembic upgrade head` and `alembic check` succeed cleanly.

---

## 5. Mandatory Unit Testing Rules for Use Cases
- **100% Use Case Test Coverage:** Every new Use Case created under `src/application/<feature>/use_cases/<use_case_name>.py` MUST have a corresponding unit test file at `tests/unit/test_<use_case_name>.py` (or `tests/unit/test_<use_case_name>_use_case.py`).
- **Isolated Mocking:** Unit tests for Use Cases MUST mock all Port interfaces (`IUnitOfWork`, `I*Repository`, external clients/publishers) using `unittest.mock.AsyncMock` or `MagicMock`—never connect to real databases or brokers in unit tests.
- **Required Scenarios:** Every Use Case test suite MUST verify:
  1. Happy path execution (repository calls, `uow.commit()`, and external side-effects).
  2. Domain rule violations and expected domain exceptions (ensuring `uow.commit()` and external calls are NOT triggered on failure).
- **CI Enforcement:** The architectural test suite (`test_every_use_case_must_have_corresponding_unit_test`) automatically fails CI if any Use Case lacks a valid unit test file with `test_*` methods.
- **Minimum 90% Code Coverage:** Core layers (`src/domain` and `src/application`) MUST maintain at least **90% branch and line coverage**. Before completing a task, run `coverage run -m unittest discover -s tests -p "test_*.py"` followed by `coverage report` to verify that coverage passes `fail_under = 90`.

---

## 6. Architectural Patterns, Helpers & Reference Examples

### Placement of Helpers & Utilities (NO Global `utils/` Folder)
- **NEVER** create generic top-level folders like `src/utils/`, `src/helpers/`, or `src/common/`.
- **Pure Python Utilities** (string formatting, math, UTC time, slugify) -> `src/domain/shared/utils.py`.
- **Domain-Specific Validators** (e.g., custom email rules) -> `src/domain/<feature>/validators.py` or inside `@dataclass(frozen=True)` Value Objects.
- **Third-Party Library Helpers** (S3 upload, Excel export, JWT) -> Define a `Protocol` in `src/application/shared/ports.py` and implement it in `src/infrastructure/`.
- **HTTP / API Helpers** (pagination wrappers, request header parsing) -> `src/presentation/api/utils.py`.

### Validation Separation
- **Presentation Layer (Pydantic):** Validate HTTP transport rules (field length, non-empty strings, raw password format) using `Field(...)` and `@field_validator` raising `ValueError` (HTTP `422`).
- **Domain Layer (Entities & Validators):** Validate core business invariants (email syntax, active status, order limits) raising `DomainError` subclasses (HTTP `400`/`409`).

### Cross-Domain Orchestration & Read Models (CQRS-Lite)
- **Multi-Domain Commands:** Orchestrate multiple domains inside `src/application/<main_feature>/use_cases/` using `IUnitOfWork` (which exposes `uow.users`, `uow.orders`, etc.). Load Entity A, call its domain validation method (e.g., `user.ensure_can_place_order()`), mutate Entity B, and commit in a single transaction.
- **Complex Read / Dashboard Queries:** Do NOT load full Domain Entities for aggregated views. Define flat Read DTOs and an `I*QueryRepository` Protocol in `src/application/<feature>/`, then implement optimized SQL JOINs/aggregations in `src/infrastructure/database/repositories/`.

### Golden Reference Implementations (Follow These Patterns)
- **Domain Entity & Custom Validator:** `src/domain/user/entities.py` & `src/domain/user/validators.py`
- **Single-Domain Use Case & DTOs:** `src/application/user/use_cases/register_user.py`
- **Cross-Domain Use Case (`User` + `Order`):** `src/application/order/use_cases/create_order.py`
- **FastAPI Router & Request Validation:** `src/presentation/api/v1/user_router.py`
