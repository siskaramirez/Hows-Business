import os
import re
import shutil
from pathlib import Path


def _version_key(path: Path):
    match = re.search(r"R-(\d+(?:\.\d+)*)", str(path))
    if not match:
        return ()
    return tuple(int(part) for part in match.group(1).split("."))


def find_rscript():
    path_from_env = shutil.which("Rscript")
    if path_from_env:
        return path_from_env

    roots = [
        Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "R",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "R",
    ]
    installed = []
    for root in roots:
        installed.extend(root.glob("R-*/bin/Rscript.exe"))
        installed.extend(root.glob("R-*/bin/x64/Rscript.exe"))

    if installed:
        return str(max(installed, key=_version_key))

    raise FileNotFoundError("Rscript was not found. Install R or add Rscript to PATH.")
