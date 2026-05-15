"""
2-2. Ollama LLaVA로 텍스트 추출
결과: results/ollama_llava/페이지명.txt

사전 준비: ollama pull llava
"""

import traceback
from pathlib import Path
import ollama

BOOK_DIR = Path("book")
OUT_DIR = Path("results/ollama_llava")
MODEL = "llava"
IMAGE_EXTENSIONS = ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]

PROMPT = (
    "이 이미지는 책 페이지 사진입니다. "
    "이미지에 있는 모든 텍스트를 빠짐없이 정확하게 추출해주세요. "
    "원문 그대로 출력하고, 설명이나 주석은 추가하지 마세요."
)


def get_sorted_images():
    images = []
    for ext in IMAGE_EXTENSIONS:
        images.extend(BOOK_DIR.glob(ext))
    images.sort(key=lambda p: [int(c) if c.isdigit() else c for c in p.stem])
    return images


if __name__ == "__main__":
    images = get_sorted_images()
    if not images:
        print(f"오류: '{BOOK_DIR}' 폴더에 이미지가 없습니다.")
        exit(1)

    print(f"이미지 {len(images)}장: {[p.name for p in images]}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for img_path in images:
        print(f"처리 중: {img_path.name}")
        try:
            with open(img_path, "rb") as f:
                img_bytes = f.read()
            response = ollama.chat(
                model=MODEL,
                messages=[{
                    "role": "user",
                    "content": PROMPT,
                    "images": [img_bytes],
                }]
            )
            text_output = response["message"]["content"]
            out_file = OUT_DIR / f"{img_path.stem}.txt"
            out_file.write_text(text_output, encoding="utf-8")
            print(f"  저장: {out_file}")
        except Exception:
            traceback.print_exc()

    print("\n완료!")
