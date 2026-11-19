# Clean Architecture Demo (Python + FastAPI + Celery + CI Guardrails)

Dự án mẫu triển khai **Clean Architecture** (tổ chức theo hướng *Feature-sliced within Layers*), được thiết kế tối ưu để vận hành cùng **AI Coding Agents**. Hệ thống đi kèm các lớp chốt chặn tự động trên CI nhằm ngăn chặn việc import chéo tầng, rò rỉ thư viện I/O vào lõi nghiệp vụ, bỏ sót Unit Test hoặc giảm độ bao phủ code dưới 90%.

---

## 1. Cấu trúc thư mục dự án

```text
clean_arch_demo/
├── .github/workflows/ci.yml       # Pipeline GitHub Actions kiểm tra CI tự động
├── alembic/                       # Quản lý lịch sử migration database
├── src/
│   ├── domain/                    # Tầng 1: Lõi nghiệp vụ thuần túy (Pure Python)
│   │   ├── shared/                # Exception & Value Object dùng chung
│   │   ├── user/                  # Entity & Exception của User
│   │   └── order/                 # Entity & Exception của Order
│   ├── application/               # Tầng 2: Use Cases & Port Interfaces (Protocol)
│   │   ├── shared/                # Interface UnitOfWork
│   │   ├── user/                  # RegisterUserUseCase, GetRecentUsersUseCase
│   │   └── order/                 # CreateOrderUseCase
│   ├── infrastructure/            # Tầng 3: Thực thi kỹ thuật (Adapters & Config)
│   │   ├── config/                # AppConfig đọc biến môi trường từ .env
│   │   ├── database/              # Models, SessionFactory (Sync/Async), Repos, UoW
│   │   ├── external/              # HTTPX Webhook Notifier
│   │   ├── messaging/             # RabbitMQ Event Publisher (aio-pika)
│   │   └── security/              # Password Hasher
│   ├── presentation/              # Tầng 4: Giao tiếp bên ngoài & Composition Root
│   │   ├── api/v1/                # FastAPI Routers (User, Order)
│   │   ├── dependencies/          # Lắp ráp Dependency Injection (DI)
│   │   └── workers/               # Celery App & Background Tasks
│   └── main.py                    # Entrypoint FastAPI kèm Lifespan quản lý DB Pool
├── tests/
│   ├── architecture/              # Quét AST kiểm tra kỷ luật kiến trúc & DI
│   └── unit/                      # Unit Test độc lập cho các Use Cases
├── AGENTS.md & CLAUDE.md          # Bộ quy tắc bắt buộc dành cho AI Agents
├── docker-compose.yml             # PostgreSQL 16 & RabbitMQ 3 Management
└── pyproject.toml                 # Cấu hình Import Linter, Ruff & Coverage
```

---

## 2. Các luồng nghiệp vụ đã tích hợp

1. **Đăng ký người dùng (`POST /api/v1/users/register`):**
   - Kiểm tra trùng email và validate dữ liệu qua `User` Entity.
   - Hash mật khẩu và lưu xuống PostgreSQL qua `UnitOfWork` (Async).
   - Gọi Webhook bên ngoài qua `HTTPX` sau khi DB đã commit (cô lập lỗi mạng để không làm hỏng giao dịch chính).
2. **Tạo đơn hàng mới (`POST /api/v1/orders/`):**
   - Kiểm tra User tồn tại thông qua `IUserRepository` (không gọi chéo Use Case).
   - Khởi tạo `Order` và `OrderItem`, tự động tính tổng tiền tại Domain Entity và lưu DB qua `UnitOfWork`.
   - Phát sự kiện `order.created` sang **RabbitMQ** sau khi transaction thành công.
3. **Lấy Top 10 User đăng ký gần nhất (Celery Worker):**
   - Task `users.fetch_top_10_recent` sử dụng **Sync Session Factory** gọi `GetRecentUsersUseCase` để truy vấn dữ liệu đồng bộ.

---

## 3. Hướng dẫn cài đặt và chạy trên Windows (PowerShell)

### Bước 1: Tạo môi trường ảo và cài thư viện
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip setuptools
pip install -r requirements.txt
pip install -e . --no-build-isolation
Copy-Item ".env.example" ".env"
```

### Bước 2: Khởi chạy PostgreSQL & RabbitMQ bằng Docker
```powershell
docker compose up -d
```
- **RabbitMQ Management UI:** `http://localhost:15672` (Tài khoản: `guest` / `guest`).

### Bước 3: Chạy Database Migration (Alembic)
```powershell
alembic revision --autogenerate -m "init_tables"
alembic upgrade head
```

### Bước 4: Khởi động API Server và Celery Worker
- **Chạy FastAPI (Terminal 1):**
  ```powershell
  uvicorn src.main:app --reload
  ```
  *(Xem tài liệu Swagger UI tại `http://127.0.0`)*.
- **Chạy Celery Worker trên Windows (Terminal 2):**
  ```powershell
  celery -A src.presentation.workers.celery_app worker --loglevel=info --pool=solo
  ```

---

## 4. Bộ chốt chặn kiểm tra CI (Bắt buộc trước khi Commit/PR)

Mọi thay đổi mã nguồn đều phải vượt qua các lệnh kiểm tra sau:

1. **Ruff Format & Lint:** Kiểm tra chuẩn PEP 8, sắp xếp import và giới hạn độ phức tạp hàm (`C901 <= 10`).
   ```powershell
   ruff format --check src tests alembic
   ruff check src tests alembic
   ```
2. **Import Linter:** Chặn import ngược tầng và cấm thư viện I/O (`sqlalchemy`, `fastapi`, `httpx`, `aio_pika`, `celery`) xâm nhập vào `domain` và `application`.
   ```powershell
   \$env:PYTHONPATH = "."
   lint-imports
   ```
3. **AST Architecture & Code Coverage Gate (>= 90%):** Quét cây cú pháp kiểm tra Type Hint trong `UseCase.__init__` (cấm dùng `Any`), cấm `print`/`open`/import động ở tầng lõi, bắt buộc 100% Use Case mới phải có Unit Test và **độ bao phủ nhánh/dòng của `src/domain` và `src/application` đạt tối thiểu 90%**.
   ```powershell
   coverage run -m unittest discover -s tests -p "test_*.py" -v
   coverage report
   ```
4. **Alembic Schema Sync:** Đảm bảo mọi thay đổi ở `models.py` đều đã có file migration tương ứng.
   ```powershell
   alembic check
   ```
