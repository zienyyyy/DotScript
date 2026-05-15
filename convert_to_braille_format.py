"""
OCR 텍스트를 점자도서관 워드입력규칙에 맞게 변환 (AI 없이 규칙 기반)

적용 규칙:
- 줄 끝 공백 제거
- 페이지 번호/머리말 줄 제거
- 장/부 제목 → @[제목@] 형식 (줄 합치기 전에 먼저 처리)
- 이어진(wrapped) 줄 합치기
- 여러 빈줄 → 1개
- 문단 시작 2칸 들여쓰기
- ~ → --
- , . : 뒤 공백 1칸 보장
- … 말줄임표 → ...
- < > [ ] 괄호 → ( )
"""

import re
import sys
from pathlib import Path

INPUT_FILE  = Path("results/gpt4o/001_test.txt")
OUTPUT_FILE = Path("results/converted/001.txt")

SENTENCE_END = re.compile(r'[.!?…。]\s*$')
PAGE_NUMBER  = re.compile(r'^.{0,20}\s+\d+\s*$')
CHAPTER_NUM  = re.compile(r'^제?\d+[장부편]\s*$')


def remove_page_numbers(lines):
    return [l for l in lines if not (PAGE_NUMBER.match(l) and len(l.strip()) < 25)]


def detect_headings(lines):
    """
    장/부 번호 줄 + 바로 다음 제목 줄을 @[N장 제목@] 으로 합친다.
    줄 합치기 전에 실행해야 한다.
    """
    result = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if CHAPTER_NUM.match(line):
            chapter_num = line
            # 다음 줄이 짧은 제목 줄이면 합침
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
    """
    문장 부호로 끝나지 않는 줄을 다음 줄과 합친다.
    @[...@] 형식(제목)이나 빈 줄은 합치지 않는다.
    """
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
            # 이어지는 줄 — 공백 하나 두고 합침
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
    # , 뒤 공백 (숫자 사이 1,000 제외)
    line = re.sub(r',(?!\s)(?!\d)', ', ', line)
    # . 뒤 공백 (소수점·말줄임표 제외)
    line = re.sub(r'\.(?!\s)(?!\d)(?!\.)', '. ', line)
    # : 뒤 공백
    line = re.sub(r':(?!\s)', ': ', line)
    # < > [ ] → ( )  (@[ ]@ 명령어는 제외)
    line = re.sub(r'(?<!@)<([^>]*)>', r'(\1)', line)
    line = re.sub(r'(?<!@)\[(?!\[)([^\]@]*)(?!\])\](?!@)', r'(\1)', line)
    return line


def add_paragraph_indent(lines):
    """빈 줄 또는 파일 시작 직후 본문 줄에 2칸 들여쓰기."""
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
    lines = detect_headings(lines)       # 줄 합치기 전에 먼저
    lines = join_wrapped_lines(lines)
    lines = collapse_blank_lines(lines)
    lines = [fix_special_chars(l) for l in lines]
    lines = add_paragraph_indent(lines)

    # 앞뒤 빈줄 제거
    while lines and lines[0].strip() == "":
        lines.pop(0)
    while lines and lines[-1].strip() == "":
        lines.pop()

    return "\n".join(lines)


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else INPUT_FILE
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else OUTPUT_FILE

    dst.parent.mkdir(parents=True, exist_ok=True)
    text = src.read_text(encoding="utf-8")
    result = convert(text)
    dst.write_text(result, encoding="utf-8")
    print(f"변환 완료: {dst}")
