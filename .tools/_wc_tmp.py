"""Temporary Prose_Word counter mirroring check_novel.count_prose_words."""

import sys
import unicodedata
from pathlib import Path


def prose_words(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    assert lines[0].strip() == "---", path
    end = lines.index("---", 1)
    prose = "\n".join(lines[end + 1 :])
    prose = unicodedata.normalize("NFC", prose.replace("\r\n", "\n").replace("\r", "\n"))
    return len(prose.split())


for argument in sys.argv[1:]:
    target = Path(argument)
    print("{0}\t{1}".format(prose_words(target), target.name))
