from typing import List

from sqlmodel import Session, select

from braid_db.models import (
    BraidDependencyModel,
    BraidRecordModel,
    BraidTagsModel,
    BraidUrisModel,
)


def test_session_creation(session: Session):
    assert session is not None


def test_create_models(session: Session):
    rec = BraidRecordModel(name="test_record")
    session.add(rec)
    session.commit()

    # Setting the record relationship via the object created above
    uri = BraidUrisModel(record=rec, uri="http://test_uri.com/id")
    session.add(uri)

    # Setting the record relationship using the record id
    tag1 = BraidTagsModel(
        record_id=rec.record_id, key="key1", value="value1", tag_type=2
    )
    tag2 = BraidTagsModel(
        record_id=rec.record_id, key="key2", value="value2", tag_type=2
    )
    session.add(tag1)
    session.add(tag2)

    session.commit()

    assert uri.record_id == rec.record_id
    assert uri.record == rec
    assert rec.uris[0] == uri
    assert rec.uri == uri

    assert tag1.record.record_id == rec.record_id
    assert tag2.record.record_id == rec.record_id

    assert tag1 in rec.tags
    assert tag2 in rec.tags

    rec2 = BraidRecordModel(name="dependent_record")
    session.add(rec2)
    session.commit()

    dependency_relationship = BraidDependencyModel(
        record_id=rec.record_id, dependency=rec2.record_id
    )
    session.add(dependency_relationship)
    session.commit()

    dependencies = session.exec(
        select(BraidDependencyModel).where(
            BraidDependencyModel.dependency == rec2.record_id
        )
    )

    dep_recs: List[BraidRecordModel] = []

    for dep in dependencies:
        dependency_id = dep.dependency
        dep_rec = session.exec(
            select(BraidRecordModel).where(
                BraidRecordModel.record_id == dependency_id
            )
        ).one_or_none()
        assert dep_rec is not None
        dep_recs.append(dep_rec)
    assert rec2 in dep_recs
