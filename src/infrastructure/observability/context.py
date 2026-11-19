import uuid
from contextvars import ContextVar

_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    return _request_id_ctx.get()


def set_request_id(request_id: str | None = None) -> str:
    cid = request_id or str(uuid.uuid4())
    _request_id_ctx.set(cid)
    return cid
