import gzip
import uuid
from datetime import datetime, timezone
from pathlib import Path


def parse(s) -> datetime:
    s = s.strip()
    if not s:
        return datetime.min.replace(tzinfo=timezone.utc)
    # Handle trailing Z
    s = s.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    # If naive, assume UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def current_time_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def exists(path: str) -> bool:
    return Path(path).exists()


def home_folder() -> str:
    return str(Path.home())


def read_gz(file: str) -> str:
    with gzip.open(file, "rt", encoding="utf-8") as f:
        return f.read()


def write_gz(file: str, data: str):
    with gzip.open(file, "wt", encoding="utf-8", compresslevel=9) as f:
        f.write(data)


def get_files(path: str, glob_pattern: str, include_path: bool = False) -> list[str]:
    folder = Path(path)
    base = folder.name

    if not include_path:
        return [file.name for file in folder.glob(glob_pattern)]

    return [
        str(Path(base) / file.relative_to(folder)) for file in folder.glob(glob_pattern)
    ]


def size_of_file(file: str) -> int:
    f = Path(file)
    return f.stat().st_size


def size_of_dir(path: str) -> int:
    folder = Path(path)
    return sum(f.stat().st_size for f in folder.glob("**/*") if f.is_file())


def generate_uuid() -> str:
    return str(uuid.uuid4())
