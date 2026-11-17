"""SQLite 历史记录：防止重复抓取、记录已生成文章。"""
import hashlib
import sqlite3
from pathlib import Path


def db_path(data_dir: str) -> Path:
    return Path(data_dir) / "history.db"


def init_db(data_dir: str) -> None:
    p = db_path(data_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS seen_items ("
        "key TEXT PRIMARY KEY, title TEXT, source TEXT, first_seen TEXT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS articles ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, title TEXT, "
        "output_file TEXT, source_urls TEXT, publish_status TEXT, created_at TEXT)"
    )
    conn.commit()
    conn.close()


def _key(item) -> str:
    if getattr(item, "url", ""):
        return item.url
    return "h:" + hashlib.md5((item.title or "").encode("utf-8")).hexdigest()


def is_seen(data_dir: str, item) -> bool:
    init_db(data_dir)
    conn = sqlite3.connect(str(db_path(data_dir)))
    cur = conn.execute("SELECT 1 FROM seen_items WHERE key=?", (_key(item),))
    found = cur.fetchone() is not None
    conn.close()
    return found


def mark_seen(data_dir: str, item) -> None:
    init_db(data_dir)
    conn = sqlite3.connect(str(db_path(data_dir)))
    conn.execute(
        "INSERT OR IGNORE INTO seen_items(key, title, source, first_seen) "
        "VALUES(?,?,?,datetime('now','localtime'))",
        (_key(item), (getattr(item, "title", "") or "")[:200], getattr(item, "source", "")),
    )
    conn.commit()
    conn.close()


def record_article(data_dir: str, date: str, title: str, output_file: str,
                   source_urls: str, publish_status: str) -> None:
    init_db(data_dir)
    conn = sqlite3.connect(str(db_path(data_dir)))
    conn.execute(
        "INSERT INTO articles(date,title,output_file,source_urls,publish_status,created_at) "
        "VALUES(?,?,?,?,?,datetime('now','localtime'))",
        (date, title, output_file, source_urls, publish_status),
    )
    conn.commit()
    conn.close()
