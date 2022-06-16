from typing import Optional

from sqlmodel import Session

from braid_db import BraidDB, BraidRecord, InvalidationActionType


def test_create_db(braid_db: BraidDB):
    braid_db.create()
    assert braid_db.engine is not None


def test_record_create(braid_db: BraidDB):
    rec = BraidRecord(braid_db, name="test_rec")
    assert rec.record_id is not None


def test_record_lookup_by_id(braid_db: BraidDB):
    rec = BraidRecord(braid_db, name="test_rec")
    assert rec.record_id is not None
    record_id = rec.record_id
    rec2 = BraidRecord.by_record_id(braid_db, record_id)
    assert rec2 is not None


def test_failed_record_lookup_by_id(braid_db: BraidDB):
    rec = BraidRecord.by_record_id(braid_db, -1)
    assert rec is None


def test_record_invalidate(braid_db: BraidDB):
    rec = BraidRecord(braid_db, name="to_be_invlidated")
    assert rec.record_id is not None
    record_id = rec.record_id
    with braid_db.get_session() as session:
        rec.invalidate("Test Cause", session=session)
        assert not rec.is_valid()
        session.commit()

    rec3 = BraidRecord.by_record_id(braid_db, record_id)
    assert not rec3.is_valid()


_test_tags = {"string_tag": "AStringVal", "int_tag": 10, "float_tag": 10.5}


def add_tags_to_record(
    rec: BraidRecord, tags=_test_tags, session: Optional[Session] = None
):
    for name, val in tags.items():
        rec.add_tag(name, val, session=session)


def test_set_get_tags(braid_db: BraidRecord):
    rec = BraidRecord(braid_db, name="tag_test_record")
    add_tags_to_record(rec)
    lookup_tags = rec.tags_as_dict()
    print(f"DEBUG {(lookup_tags)=}")


def test_tag_create_and_lookup(braid_db: BraidDB):
    rec1 = BraidRecord(braid_db, name="Record1")
    assert rec1.record_id is not None
    tag_id = rec1.add_tag("test_tag", "test_value")
    assert tag_id > 0

    with braid_db.get_session() as session:
        recs_by_tag = BraidRecord.for_tag_value(
            braid_db, "test_tag", "test_value", session
        )
        found = False
        for found_rec in recs_by_tag:
            if found_rec.record_id == rec1.record_id:
                found = True
                break
        assert found


def test_tag_create_and_invalidate(braid_db: BraidDB):
    rec1 = BraidRecord(braid_db, name="Record1")
    assert rec1.record_id is not None
    rec1_id = rec1.record_id
    tag_id = rec1.add_tag("test_tag", "test_value")
    assert tag_id > 0

    rec2 = BraidRecord(braid_db, name="Record2")
    assert rec1.record_id is not None
    rec2_id = rec2.record_id
    tag_id = rec1.add_tag("test_tag", "not_the_test_value")
    assert tag_id > 0

    with braid_db.get_session() as session:
        BraidRecord.invalidate_by_tag_value(
            braid_db, "test_tag", "test_value", session
        )
        session.commit()

    rec1_lookup = BraidRecord.by_record_id(braid_db, rec1_id)
    assert rec1_lookup is not None
    assert not rec1_lookup.is_valid()

    rec2_lookup = BraidRecord.by_record_id(braid_db, rec2_id)
    assert rec2_lookup is not None
    assert rec2_lookup.is_valid()


def test_invalidate_action(braid_db: BraidDB, monkeypatch):
    with braid_db.get_session() as session:
        irec = BraidRecord(braid_db, name="To Be Invalidated")
        assert irec.record_id is not None
        invalidation_action = irec.add_invalidation_action(
            InvalidationActionType.SHELL_COMMAND,
            "invalidation shell command",
            "echo",
            {"args": ["Hello", "{name}"]},
            session=session,
        )
        session.commit()
        assert invalidation_action is not None
        irec.invalidate("Cause this is a test", session=session)
