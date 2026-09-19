"""ingestion 脚本:python scripts/ingest_corpus.py [--corpus data/corpus] [--db data/freshlatch.db]"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from freshlatch.store.ingest import ingest_into  # noqa: E402
from freshlatch.store.sqlite_store import SQLiteStore  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="data/corpus")
    ap.add_argument("--db", default="data/freshlatch.db")
    args = ap.parse_args()

    store = SQLiteStore(args.db)
    n = ingest_into(store, Path(args.corpus))
    print(f"ingested {n} chunks into {args.db}")


if __name__ == "__main__":
    main()
