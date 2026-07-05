import os
import tempfile

from modules.api_services import JobStore, require_api_auth


class DummyRequest:
    def __init__(self, headers=None):
        self.headers = headers or {}


def test_job_store_persists_and_updates(tmp_path):
    store_path = tmp_path / 'jobs.json'
    store = JobStore(str(store_path))

    job_id = store.create(status='queued', payload={'prompt': 'hello'})
    store.update(job_id, status='running', progress=25)

    reloaded = JobStore(str(store_path))
    job = reloaded.get(job_id)

    assert job['status'] == 'running'
    assert job['progress'] == 25
    assert job['payload']['prompt'] == 'hello'


def test_require_api_auth_accepts_valid_bearer_token():
    assert require_api_auth(DummyRequest(), token=None) is True
    assert require_api_auth(DummyRequest(), token='secret') is False
    assert require_api_auth(DummyRequest({'authorization': 'Bearer secret'}), token='secret') is True
    assert require_api_auth(DummyRequest({'authorization': 'Bearer wrong'}), token='secret') is False
