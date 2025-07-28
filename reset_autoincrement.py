from sqlalchemy import text

from tests.conftest import engine

with engine.connect() as conn:
    try:
        conn.execute(text('DELETE FROM sqlite_sequence WHERE name="documents"'))
        conn.commit()
        print("Reset auto-increment for documents table")
    except Exception as e:
        print(f"Error: {e}")
