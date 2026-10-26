from sqlalchemy.orm import Session


def commit(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
