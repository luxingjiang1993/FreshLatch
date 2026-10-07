"""ingestion 脚本:python scripts/ingest_corpus.py [--corpus ...] [--db ...]

默认路径来自 active_pack(未设置环境变量时为第一课题)。
"""

from __future__ import annotations

import argparse
from pathlib import Path

from freshlatch.packs import resolve_pack  # noqa: E402
from freshlatch.store.ingest import ingest_into  # noqa: E402
from freshlatch.store.local_embed import attach_local_embedder  # noqa: E402
from freshlatch.store.sqlite_store import SQLiteStore  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    pack = resolve_pack()
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=str(pack.corpus))
    ap.add_argument("--db", default=str(pack.sqlite))
    return ap


def main() -> None:
    args = build_parser().parse_args()

    store = SQLiteStore(args.db)
    attach_local_embedder(store)
    n = ingest_into(store, Path(args.corpus))
    print(f"ingested {n} chunks into {args.db}")


if __name__ == "__main__":
    main()
