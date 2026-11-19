# AGENTS.md - Clean Architecture & Engineering Rules

You are working on a Python 3.12 project strictly following **Clean Architecture** (Feature-sliced within Layers). Any code you generate or modify MUST pass all static analysis and architectural gates in CI.

---

## 1. Architectural Layer Boundaries (Strict Dependency Rule)

Dependencies MUST ONLY point inwards:
`src.presentation` -> `src.infrastructure` -> `src.application` -> `src.domain`

### `src/domain/` (Core Business Logic)
- **Allowed:** Pure Python standard library (`dataclasses`, `typing`, `uuid`, `datetime`, `decimal`, `enum`) and `src.domain.shared`.
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

### `src/infrastructure/` (Adapters & Configuration)
- **Allowed:** Implements interfaces defined in `src.application` using concrete libraries (`SQLAlchemy`, `HTTPX`, `aio-pika`, `pydantic-settings`).
- **Rules:**
  - Repositories (`sqlalchemy_*_repo.py`) MUST map between ORM Models and Domain Entities, and call `await session.flush()` instead of `commit()` (transaction commits belong to `UnitOfWork`).
  - Environment variables MUST only be accessed via `AppConfig` (`src/infrastructure/config/app_config.py`). If adding a new env variable, update `AppConfig` and `.env.example` ONLY (never modify `.env`).

### `src/presentation/` (FastAPI Routers, Celery Workers & Composition Root)
- **Allowed:** FastAPI routers (`api/v1/`), Celery tasks (`workers/`), and Dependency Injection wiring (`dependencies/`).
- **Rules:**
  - FastAPI endpoints and Celery tasks MUST NOT contain business logic or direct database queries. They only parse input DTOs, invoke a `UseCase`, and map domain exceptions to HTTP responses or task outputs.

---

## 2. Coding Standards & Complexity Limits
- **Line length:** Maximum `100` characters.
- **Function complexity:** McCabe complexity (`C901`) MUST NOT exceed `10`. Break large functions into small, focused helper methods.
- **Type annotations:** All function signatures and return types MUST be explicitly typed.

---

## 3. Mandatory Pre-Completion Verification
Before finishing any task or submitting code, you MUST run and pass all four commands below with zero errors:

```bash
ruff format --check src tests
ruff check src tests
lint-imports
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
