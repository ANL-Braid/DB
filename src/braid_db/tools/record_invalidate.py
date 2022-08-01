import argparse

from braid_db import BraidDB, BraidRecord


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("db_file", type=str, nargs=1)
    parser.add_argument("cause", type=str, nargs=1)
    parser.add_argument("record_ids", type=int, nargs="*")

    args = parser.parse_args()

    db = BraidDB(args.db_file[0])
    cause = args.cause[0]
    session = db.get_session()
    for record_id in args.record_ids:
        rec = BraidRecord.by_record_id(db, record_id, session=session)
        print(f"Invalidating record id {record_id} with name {rec.name}")
        rec.invalidate(cause=cause, session=session)
    session.commit()


if __name__ == "__main__":
    main()
