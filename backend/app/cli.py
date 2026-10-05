"""Command-line imports, for tools that feed the archive on a schedule instead of through the upload page.

    python -m backend.app.cli sync NAME < export.json

`sync` parses the file like an upload but files everything under one standing import called "sync: NAME", so a
feed that runs every hour shows as a single row in the importer instead of hundreds. Deleting that row removes
what the feed brought in, as with any import. The file itself is not kept.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from .db import RAW_DIR, connect, init_db, utcnow
from .main import process_import


def sync(name: str, data: bytes) -> dict:
    init_db()
    label = f"sync: {name}"
    with connect() as conn:
        row = conn.execute("SELECT id FROM imports WHERE original_filename = ? ORDER BY id LIMIT 1", (label,)).fetchone()
        if row:
            import_id = int(row["id"])
        else:
            cursor = conn.execute(
                "INSERT INTO imports(filename, original_filename, sha256, status, created_at) VALUES (?, ?, ?, ?, ?)",
                (label, label, "-", "queued", utcnow()),
            )
            import_id = int(cursor.lastrowid)
        conn.commit()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=RAW_DIR, prefix="sync-", suffix=".json", delete=False) as handle:
        handle.write(data)
        path = Path(handle.name)
    try:
        process_import(import_id, str(path))
    finally:
        path.unlink(missing_ok=True)
    with connect() as conn:
        row = conn.execute("SELECT status, error, summary_json FROM imports WHERE id = ?", (import_id,)).fetchone()
    return {"import_id": import_id, "status": row["status"], "error": row["error"],
            "summary": json.loads(row["summary_json"] or "{}")}


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "sync" or not argv[1].strip():
        print(__doc__.strip(), file=sys.stderr)
        return 2
    result = sync(argv[1].strip(), sys.stdin.buffer.read())
    print(json.dumps(result))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
