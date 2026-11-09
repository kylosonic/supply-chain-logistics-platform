from app.core.observability import AppMetrics


def test_unhandled_exception_counter_and_timestamp_are_recorded():
    metrics = AppMetrics()
    assert metrics.snapshot()['unhandled_exceptions'] == 0
    assert metrics.snapshot()['last_exception_at'] is None

    metrics.record_exception()

    snapshot = metrics.snapshot()
    assert snapshot['unhandled_exceptions'] == 1
    assert snapshot['last_exception_at'] is not None
