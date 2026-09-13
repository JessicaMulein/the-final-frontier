"""Temporary Prose_Word counter mirroring check_novel.count_prose_words."""
import sys
import unicodedata

for path in sys.argv[1:]:
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    body = text.split("---", 2)[2]
    normalized = unicodedata.normalize("NFC", body.replace("\r\n", "\n").replace("\r", "\n"))
    print(len(normalized.split()), path.rsplit("/", 1)[-1])
