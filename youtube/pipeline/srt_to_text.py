import re
from pathlib import Path

# Matches timestamp lines like:
# 00:00:01,000 --> 00:00:03,000
TIMESTAMP = re.compile(
    r"^\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}.*$",
    re.MULTILINE,
)


def srt_to_text(srt_path: Path) -> str:
    text = srt_path.read_text(encoding="utf-8", errors="ignore")

    # Drop sequence numbers (lines that are only digits)
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)

    # Drop timestamp lines
    text = re.sub(TIMESTAMP, "", text)

    # Drop simple tags like <i>...</i>
    text = re.sub(r"<[^>]+>", "", text)

    # Collapse whitespace
    return " ".join(text.split())


def main():
    script_dir = Path(__file__).resolve().parent
    outroot = Path((script_dir / "../transcripts").resolve())

    converted = 0
    for srt in outroot.rglob("*.srt"):
        txt_path = srt.with_suffix(".txt")
        txt_path.write_text(srt_to_text(srt), encoding="utf-8")
        converted += 1
        print(f"Converted: {txt_path}")

    print(f"Done. Converted {converted} files.")


if __name__ == "__main__":
    main()
