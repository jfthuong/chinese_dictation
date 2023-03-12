import contextlib
from pathlib import Path
from typing import Generator, Optional
from tempfile import NamedTemporaryFile


@contextlib.contextmanager
def temporary_filename(suffix=None, prefix=None) -> Generator[Path, None, None]:
    """Context that introduces a temporary file.

    Creates a temporary file, yields its name, and upon context exit, deletes it.
    (In contrast, tempfile.NamedTemporaryFile() provides a 'file' object and
    deletes the file as soon as that file object is closed, so the temporary file
    cannot be safely re-opened by another library or process.)

    Args:
        suffix: desired filename extension (e.g. '.mp4').
        prefix: desired filename prefix (e.g. 'video_').

    Yields:
        The name of the temporary file.
    """
    tmp: Optional[Path] = None
    try:
        f = NamedTemporaryFile(suffix=suffix, prefix=prefix, delete=False)
        tmp = Path(f.name)
        f.close()
        yield tmp
    finally:
        if tmp:
            tmp.unlink()
