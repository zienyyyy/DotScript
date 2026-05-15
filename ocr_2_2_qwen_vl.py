"""
2-2. Ollama Qwen2.5-VL로 텍스트 추출
결과: results/qwen_vl/페이지명.txt

사전 준비: ollama pull qwen2.5vl:7b
"""

import traceback
from pathlib import Path
import ollama

BOOK_DIR = Path("book")
OUT_DIR = Path("results/qwen_vl")
MODEL = "qwen2.5vl:7b"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

PROMPT = (
    "Please transcribe all the text visible in this image exactly as it appears, "
    "preserving line breaks. Output only the transcribed text with no commentary."
)


def get_sorted_images():
    images = [p for p in BOOK_DIR.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS]
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
