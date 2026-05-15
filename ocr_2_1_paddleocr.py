"""
2-1. PaddleOCR로 텍스트 추출
결과: results/paddleocr/페이지명.txt
"""

import traceback
from pathlib import Path
from paddleocr import PaddleOCR

BOOK_DIR = Path("book")
OUT_DIR = Path("results/paddleocr")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


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

    ocr = PaddleOCR(use_angle_cls=True, lang="korean", show_log=False)

    for img_path in images:
        print(f"처리 중: {img_path.name}")
        try:
            result = ocr.ocr(str(img_path), cls=True)  # noqa: deprecated
            lines = []
            if result and result[0]:
                for line in result[0]:
                    lines.append(line[1][0])
            out_file = OUT_DIR / f"{img_path.stem}.txt"
            out_file.write_text("\n".join(lines), encoding="utf-8")
            print(f"  저장: {out_file}")
        except Exception:
            traceback.print_exc()

    print("\n완료!")
