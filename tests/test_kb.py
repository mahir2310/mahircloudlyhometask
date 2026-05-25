from app import kb


def test_snapshot_and_aggregate():
    # Ensure DB functions run; snapshot should return a list
    snap = kb.snapshot_top_n(2)
    assert isinstance(snap, list)
    agg = kb.aggregate_wrong_counts()
    assert isinstance(agg, dict)
