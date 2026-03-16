import os
import pymysql


def init_schema():
    """Create all DB tables from schema.sql on first run.
    Skips DROP TABLE statements and ignores errors for already-existing tables/indexes."""
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'schema.sql')
    with open(schema_path, 'r') as f:
        raw = f.read()

    conn = pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASS"],
        database=os.environ["DB_BASE"],
        charset='utf8',
        autocommit=True,
    )
    try:
        cursor = conn.cursor()
        for stmt in raw.split(';'):
            # Strip comment lines and whitespace
            lines = [l for l in stmt.split('\n') if not l.strip().startswith('--')]
            stmt = ' '.join(lines).strip()
            if not stmt:
                continue
            upper = stmt.upper().lstrip()
            # Skip DROP TABLE — preserve data on restart
            if upper.startswith('DROP TABLE') or upper.startswith('DROP DATABASE'):
                continue
            try:
                cursor.execute(stmt)
            except pymysql.err.OperationalError as e:
                # 1050 = table already exists
                # 1061 = duplicate key name
                # 1060 = duplicate column name
                if e.args[0] not in (1050, 1061, 1060):
                    print(f"[init_schema] OperationalError {e.args[0]}: {e.args[1]}")
            except pymysql.err.ProgrammingError as e:
                # 1007 = database exists
                if e.args[0] != 1007:
                    print(f"[init_schema] ProgrammingError {e.args[0]}: {e.args[1]}")
            except Exception:
                pass  # Ignore comment-only fragments and other noise
        cursor.close()
    finally:
        conn.close()
