#!python3
import time
import tor_elasticsearch

MAX_RETRIES = 10
RETRY_DELAY = 15

for attempt in range(1, MAX_RETRIES + 1):
    try:
        tor_elasticsearch.migrate()
        print("[elasticsearch_migrate] Migration successful.")
        break
    except Exception as e:
        print(f"[elasticsearch_migrate] Attempt {attempt}/{MAX_RETRIES} failed: {e}")
        if attempt < MAX_RETRIES:
            print(f"[elasticsearch_migrate] Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
        else:
            print("[elasticsearch_migrate] All retries exhausted. Continuing without ES migration.")
