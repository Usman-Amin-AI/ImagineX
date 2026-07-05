import json
import os
from typing import Any, Dict, Optional


class JobStore:
    def __init__(self, path: Optional[str] = None):
        self.path = path or os.environ.get('IMAGINEX_JOB_STORE', 'outputs/jobs.json')
        self._ensure_parent()
        self._data: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _ensure_parent(self) -> None:
        parent = os.path.dirname(self.path)
        if parent:
            os.makedirs(parent, exist_ok=True)

    def _load(self) -> None:
        if not os.path.exists(self.path):
            self._data = {}
            return
        try:
            with open(self.path, 'r', encoding='utf-8') as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                self._data = loaded
        except Exception:
            self._data = {}

    def _save(self) -> None:
        with open(self.path, 'w', encoding='utf-8') as handle:
            json.dump(self._data, handle, indent=2)

    def create(self, *, status: str = 'queued', payload: Optional[Dict[str, Any]] = None, **extra) -> str:
        import uuid

        job_id = uuid.uuid4().hex
        self._data[job_id] = {'id': job_id, 'status': status, 'progress': 0, 'payload': payload or {}, **extra}
        self._save()
        return job_id

    def update(self, job_id: str, **updates) -> None:
        if job_id not in self._data:
            return
        self._data[job_id].update(updates)
        self._save()

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self._data.get(job_id)


def require_api_auth(request, token: Optional[str] = None) -> bool:
    if token is None:
        return True

    auth_header = request.headers.get('authorization', '') if getattr(request, 'headers', None) else ''
    if not auth_header:
        return False
    if not auth_header.lower().startswith('bearer '):
        return False
    return auth_header.split(' ', 1)[1].strip() == token
