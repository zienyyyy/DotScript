"""
Qwen OCR 결과를 점자도서관 워드입력규칙에 맞게 변환
입력: results/qwen_vl/*.txt
출력: results/qwen_converted/*.txt
"""

import re
import sys
from pathlib import Path

IN_DIR  = Path("results/qwen_vl")
OUT_DIR = Path("results/qwen_converted")

SENTENCE_END = re.compile(r'[.!?…。]\s*$')
PAGE_NUMBER  = re.compile(r'^.{0,20}\s+\d+\s*$')
CHAPTER_NUM  = re.compile(r'^제?\d+[장부편]\s*$')


def remove_page_numbers(lines):
    return [l for l in lines if not (PAGE_NUMBER.match(l) and len(l.strip()) < 25)]


def detect_headings(lines):
    result = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if CHAPTER_NUM.match(line):
            chapter_num = line
            if (i + 1 < len(lines) and
                    lines[i + 1].strip() and
                    not SENTENCE_END.search(lines[i + 1]) and
                    len(lines[i + 1].strip()) <= 20):
                title = lines[i + 1].strip()
                result.append(f"@[{chapter_num} {title}@]")
                i += 2
            else:
                result.append(f"@[{chapter_num}@]")
                i += 1
        else:
            result.append(lines[i])
            i += 1
    return result


def join_wrapped_lines(lines):
    result = []
    buf = ""
    for line in lines:
        stripped = line.strip()
        if stripped == "":
            if buf:
                result.append(buf)
                buf = ""
            result.append("")
        elif stripped.startswith("@["):
            if buf:
                result.append(buf)
                buf = ""
            result.append(line)
        elif SENTENCE_END.search(stripped):
            buf = (buf + " " + stripped).strip() if buf else stripped
            result.append(buf)
            buf = ""
        else:
            buf = (buf + " " + stripped).strip() if buf else stripped
    if buf:
        result.append(buf)
    return result


def collapse_blank_lines(lines):
    result = []
    prev_blank = False
    for line in lines:
        is_blank = line.strip() == ""
        if is_blank and prev_blank:
            continue
        result.append(line)
        prev_blank = is_blank
    return result


def fix_special_chars(line):
    line = re.sub(r'~', '--', line)
    line = re.sub(r'[…]+', '...', line)
    line = re.sub(r'\.{4,}', '...', line)
    line = re.sub(r',(?!\s)(?!\d)', ', ', line)
    line = re.sub(r'\.(?!\s)(?!\d)(?!\.)', '. ', line)
    line = re.sub(r':(?!\s)', ': ', line)
    line = re.sub(r'(?<!@)<([^>]*)>', r'(\1)', line)
    line = re.sub(r'(?<!@)\[(?!\[)([^\]@]*)(?!\])\](?!@)', r'(\1)', line)
    return line


def add_paragraph_indent(lines):
    result = []
    prev_blank = True
    for line in lines:
        if line.strip() == "":
            result.append(line)
            prev_blank = True
        elif prev_blank and not line.startswith("  ") and not line.startswith("@"):
            result.append("  " + line)
            prev_blank = False
        else:
            result.append(line)
            prev_blank = False
    return result


def convert(text):
    lines = [l.rstrip() for l in text.splitlines()]
    lines = remove_page_numbers(lines)
    lines = detect_headings(lines)
    lines = join_wrapped_lines(lines)
    lines = collapse_blank_lines(lines)
    lines = [fix_special_chars(l) for l in lines]
    lines = add_paragraph_indent(lines)

    while lines and lines[0].strip() == "":
        lines.pop(0)
    while lines and lines[-1].strip() == "":
        lines.pop()

    return "\n".join(lines)


if __name__ == "__main__":
    src_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else IN_DIR
    dst_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT_DIR

    txt_files = sorted(src_dir.glob("*.txt"))
    if not txt_files:
        print(f"오류: '{src_dir}'에 txt 파일이 없습니다.")
        exit(1)

    dst_dir.mkdir(parents=True, exist_ok=True)
    print(f"{len(txt_files)}개 파일 변환 중...")

    for src in txt_files:
        dst = dst_dir / src.name
        text = src.read_text(encoding="utf-8")
        result = convert(text)
        dst.write_text(result, encoding="utf-8")
        print(f"  {src.name} → {dst}")

    print("완료!")
