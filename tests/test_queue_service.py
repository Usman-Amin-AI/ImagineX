from modules.queue_services import QueueManager


def test_queue_manager_enqueues_and_reports_status(tmp_path):
    manager = QueueManager(storage_path=str(tmp_path / 'queue.json'), backend='memory')

    job_id = manager.enqueue('demo_task', payload={'prompt': 'hello'})
    status = manager.get_job_status(job_id)

    assert status['id'] == job_id
    assert status['status'] in {'queued', 'running', 'done', 'failed'}
    assert status['payload']['prompt'] == 'hello'
