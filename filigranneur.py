#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF


def add_watermark_to_image(image_path, text, logo_path=None):
    img = Image.open(image_path).convert("RGBA")

    # Création d'une couche transparente
    txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)

    width, height = img.size

    # Police (fallback si Arial non dispo)
    try:
        font = ImageFont.truetype("arial.ttf", int(width / 20))
    except:
        font = ImageFont.load_default()

    # Position centrée
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    position = ((width - text_width) / 2, (height - text_height) / 2)

    # Texte semi-transparent
    draw.text(position, text, fill=(255, 0, 0, 100), font=font)

    # Logo optionnel
    if logo_path and Path(logo_path).exists():
        logo = Image.open(logo_path).convert("RGBA")

        # Resize logo
        logo.thumbnail((width // 5, height // 5))

        lx, ly = logo.size
        logo_position = (width - lx - 10, height - ly - 10)

        txt_layer.paste(logo, logo_position, logo)

    # Fusion
    watermarked = Image.alpha_composite(img, txt_layer)

    output_path = image_path.with_stem(image_path.stem + "_watermarked")
    watermarked.convert("RGB").save(output_path)

    print(f"✔ Image sauvegardée : {output_path}")


def add_watermark_to_pdf(pdf_path, text, logo_path=None):
    doc = fitz.open(pdf_path)

    for page in doc:
        width = page.rect.width
        height = page.rect.height

        # Texte centré
        page.insert_text(
            (width / 4, height / 2),
            text,
            fontsize=30,
            rotate=0,
            color=(1, 0, 0),
            fill_opacity=0.2,
        )

        # Logo optionnel
        if logo_path and Path(logo_path).exists():
            rect = fitz.Rect(width - 150, height - 150, width - 10, height - 10)
            page.insert_image(rect, filename=logo_path)

    output_path = pdf_path.with_stem(pdf_path.stem + "_watermarked")
    doc.save(output_path)

    print(f"✔ PDF sauvegardé : {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 filigranneur.py 'texte' [logo.png]")
        sys.exit(1)

    text = sys.argv[1]
    logo_path = sys.argv[2] if len(sys.argv) > 2 else None

    # Parcours des fichiers du dossier courant
    for file in Path(".").iterdir():
        if file.suffix.lower() in [".jpg", ".jpeg", ".png"]:
            add_watermark_to_image(file, text, logo_path)

        elif file.suffix.lower() == ".pdf":
            add_watermark_to_pdf(file, text, logo_path)


if __name__ == "__main__":
    main()
