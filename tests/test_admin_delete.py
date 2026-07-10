from src.handlers.admin import build_delete_message_ids


def test_build_delete_message_ids_with_reply_only() -> None:
    ids = build_delete_message_ids(reply_message_id=42, recent_ids=[10, 20, 30], requested_count=1)
    assert ids == [42]


def test_build_delete_message_ids_with_requested_count() -> None:
    ids = build_delete_message_ids(reply_message_id=42, recent_ids=[10, 20, 30, 40], requested_count=3)
    assert ids == [42, 10, 20]
