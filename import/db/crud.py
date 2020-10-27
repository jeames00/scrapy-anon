from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker, load_only
from sqlalchemy import create_engine, PrimaryKeyConstraint, UniqueConstraint
from scrapyanon.db.db_config import DATABASE_URI
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.sql import func

engine = create_engine(DATABASE_URI, echo=True)
Session = sessionmaker(bind=engine)

@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def upsert(session, model, rows, constraint):
    table = model.__table__
    stmt = postgresql.insert(table)
    insp = Inspector.from_engine(engine)
    unique_keys = list(c.name for c in table.columns if c.unique)
    primary_keys = list(c.name for c in table.columns if c.primary_key)

    update_cols = {
        c.name: c
        for c in stmt.excluded
        if not c.primary_key
    }

    stmt = stmt.on_conflict_do_update(
        constraint = constraint,
        set_ = update_cols,
    )

    checked_rows = set()
    def check_duplicates(row):
        for unique_col in unique_keys:
            unique = tuple([unique_col,] + [row[unique_col]])
            if unique in checked_rows:
                print("skipping duplicate row: " + str(unique))
                return None
            checked_rows.add(unique)

        return row

    rows = list(filter(None, (check_duplicates(row) for row in rows)))

    session.execute(stmt, rows)

def get_random_id(session, model):
    random = session.query(model).options(load_only('id')).order_by(func.random()).first()
    return random.id
