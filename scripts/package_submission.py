"""Prepare, but do not upload, the assignment submission ZIP."""

import argparse
from pathlib import Path
import re
import zipfile


ROOT = Path(__file__).resolve().parents[1]
INCLUDED_DIRS = ("src", "assets", "data", "docs", "experiments", "tests", "scripts")
ROOT_FILES = (
    "README.md", "PROJECT_STRUCTURE.md", "pyproject.toml", "requirements.txt",
    ".python-version", "Play.cmd", "CHANGELOG.md",
)


def main():
    parser = argparse.ArgumentParser(description="Prepare a local submission ZIP; this never uploads it.")
    parser.add_argument("--registration", action="append", required=True, help="Member registration number; repeat per member")
    parser.add_argument("--section", required=True)
    args = parser.parse_args()
    if not 1 <= len(args.registration) <= 3:
        parser.error("provide one to three registration numbers")
    if any(not re.fullmatch(r"[A-Za-z0-9-]+", value) for value in args.registration + [args.section]):
        parser.error("registration numbers and section may contain only letters, numbers and hyphens")
    executable = ROOT / "dist" / "SmartRacingChampionship.exe"
    report = ROOT / "output" / "pdf" / "technical-report.pdf"
    for path in (executable, report):
        if not path.is_file():
            parser.error(f"required artifact not found: {path}")
    output = ROOT / "dist" / ("_".join(args.registration + [args.section]) + ".zip")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(executable, "SmartRacingChampionship.exe")
        archive.write(report, "technical-report.pdf")
        for name in ROOT_FILES:
            archive.write(ROOT / name, "source/" + name)
        for name in INCLUDED_DIRS:
            for path in (ROOT / name).rglob("*"):
                if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                    archive.write(path, "source/" + path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(output) as archive:
        bad_file = archive.testzip()
        if bad_file:
            raise RuntimeError(f"Corrupted ZIP entry: {bad_file}")
    print(f"Created and checked {output}; no upload was performed.")


if __name__ == "__main__":
    main()
