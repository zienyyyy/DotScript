"""
2-3. GPT-4o API로 텍스트 추출
결과: results/gpt4o/페이지명.txt

사전 준비: .env 파일에 OPENAI_API_KEY=sk-... 입력
"""

import os
import base64
import traceback
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BOOK_DIR = Path("book")
OUT_DIR = Path("results/gpt4o")
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


def encode_image_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


if __name__ == "__main__":
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("오류: .env 파일에 OPENAI_API_KEY가 없습니다.")
        exit(1)

    images = get_sorted_images()
    if not images:
        print(f"오류: '{BOOK_DIR}' 폴더에 이미지가 없습니다.")
        exit(1)

    print(f"이미지 {len(images)}장: {[p.name for p in images]}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    client = OpenAI(api_key=api_key)

    for img_path in images:
        print(f"처리 중: {img_path.name}")
        try:
            b64 = encode_image_base64(img_path)
            ext = img_path.suffix.lower().lstrip(".")
            mime = "jpeg" if ext in ("jpg", "jpeg") else ext

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/{mime};base64,{b64}",
                            "detail": "high"
                        }},
                    ],
                }],
                max_tokens=4096,
            )
            text_output = response.choices[0].message.content
            out_file = OUT_DIR / f"{img_path.stem}.txt"
            out_file.write_text(text_output, encoding="utf-8")
            print(f"  저장: {out_file}")
        except Exception:
            traceback.print_exc()

    print("\n완료!")
