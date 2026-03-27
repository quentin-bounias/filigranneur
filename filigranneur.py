#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import math
import sys
from io import BytesIO
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Ajoute un filigrane texte répété en diagonale sur images et PDF."
    )

    # Compatibilité avec ton usage initial :
    # python3 filigranneur.py "Texte" "logo.png"
    parser.add_argument("text", help="Texte du filigrane")
    parser.add_argument(
        "logo",
        nargs="?",
        default=None,
        help="Chemin du logo optionnel (png recommandé)",
    )

    parser.add_argument(
        "--input",
        default=".",
        help="Fichier ou dossier à traiter (défaut: dossier courant)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Dossier de sortie (défaut: même dossier que le fichier source)",
    )
    parser.add_argument(
        "--opacity",
        type=int,
        default=55,
        help="Opacité du texte entre 0 et 255 (défaut: 55)",
    )
    parser.add_argument(
        "--logo-opacity",
        type=int,
        default=160,
        help="Opacité du logo entre 0 et 255 (défaut: 160)",
    )
    parser.add_argument(
        "--font-size",
        type=int,
        default=None,
        help="Taille de police. Si absente, calcul automatique.",
    )
    parser.add_argument(
        "--font-path",
        default=None,
        help="Chemin vers un fichier .ttf/.otf (ex: Bebas Neue).",
    )
    parser.add_argument(
        "--color",
        default="180,0,0",
        help="Couleur du texte au format R,G,B (défaut: 180,0,0)",
    )
    parser.add_argument(
        "--angle",
        type=float,
        default=35,
        help="Angle du filigrane en degrés (défaut: 35)",
    )
    parser.add_argument(
        "--spacing-x",
        type=int,
        default=None,
        help="Espacement horizontal entre répétitions",
    )
    parser.add_argument(
        "--spacing-y",
        type=int,
        default=None,
        help="Espacement vertical entre répétitions",
    )
    parser.add_argument(
        "--logo-scale",
        type=float,
        default=0.14,
        help="Taille du logo par rapport à la largeur (défaut: 0.14)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=160,
        help="Résolution de rendu des PDF (défaut: 160). Plus haut = plus propre mais plus lourd.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Parcourt récursivement les sous-dossiers",
    )

    return parser.parse_args()


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def parse_rgb(rgb_string):
    try:
        parts = [int(x.strip()) for x in rgb_string.split(",")]
        if len(parts) != 3:
            raise ValueError
        return tuple(clamp(v, 0, 255) for v in parts)
    except Exception:
        raise ValueError("La couleur doit être au format R,G,B, ex: 180,0,0")


def find_default_font(user_font_path=None):
    """
    Priorité :
    1. police fournie explicitement
    2. Bebas Neue si trouvée localement
    3. polices de fallback courantes
    """
    candidates = []

    if user_font_path:
        candidates.append(user_font_path)

    candidates.extend(
        [
            # Bebas Neue - chemins fréquents selon OS / installation manuelle
            "./BebasNeue-Regular.ttf",
            "./BebasNeue-Regular.otf",
            "/Library/Fonts/BebasNeue-Regular.ttf",
            "/Library/Fonts/BebasNeue-Regular.otf",
            str(Path.home() / "Library/Fonts/BebasNeue-Regular.ttf"),
            str(Path.home() / "Library/Fonts/BebasNeue-Regular.otf"),
            "/usr/share/fonts/truetype/bebas/BebasNeue-Regular.ttf",
            "/usr/share/fonts/opentype/bebas/BebasNeue-Regular.otf",
            # Fallbacks
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ]
    )

    for path in candidates:
        if path and Path(path).exists():
            return path

    return None


def load_font(font_path, font_size):
    if font_path:
        try:
            return ImageFont.truetype(font_path, font_size)
        except Exception:
            pass

    try:
        return ImageFont.load_default()
    except Exception as exc:
        raise RuntimeError(f"Impossible de charger une police: {exc}")


def apply_alpha_to_rgba(image_rgba, alpha_value):
    """Applique une opacité globale à une image RGBA."""
    alpha_value = clamp(alpha_value, 0, 255)
    if image_rgba.mode != "RGBA":
        image_rgba = image_rgba.convert("RGBA")

    r, g, b, a = image_rgba.split()
    a = a.point(lambda px: int(px * alpha_value / 255))
    return Image.merge("RGBA", (r, g, b, a))


def build_watermark_tile(text, font, color_rgb, opacity):
    """
    Crée une petite tuile contenant le texte.
    Cette tuile sera répétée sur toute la surface puis tournée.
    """
    dummy = Image.new("RGBA", (10, 10), (255, 255, 255, 0))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox((0, 0), text, font=font)

    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    tile_w = max(text_w + 80, 200)
    tile_h = max(text_h + 50, 100)

    tile = Image.new("RGBA", (tile_w, tile_h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(tile)
    draw.text(
        (40, 20),
        text,
        font=font,
        fill=(color_rgb[0], color_rgb[1], color_rgb[2], clamp(opacity, 0, 255)),
    )
    return tile, text_w, text_h


def create_text_overlay(
    base_size, text, font, color_rgb, opacity, angle, spacing_x=None, spacing_y=None
):
    width, height = base_size

    tile, text_w, text_h = build_watermark_tile(text, font, color_rgb, opacity)

    if spacing_x is None:
        spacing_x = max(int(text_w * 1.2), 220)

    if spacing_y is None:
        spacing_y = max(int(text_h * 3.2), 140)

    # On crée une grande surface avant rotation pour couvrir toute l'image finale
    diagonal = int(math.sqrt(width * width + height * height))
    big_w = diagonal * 2
    big_h = diagonal * 2

    repeated = Image.new("RGBA", (big_w, big_h), (255, 255, 255, 0))

    for y in range(0, big_h, spacing_y):
        row_offset = 0 if (y // spacing_y) % 2 == 0 else spacing_x // 2
        for x in range(-spacing_x, big_w, spacing_x):
            repeated.alpha_composite(tile, (x + row_offset, y))

    rotated = repeated.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)

    left = (rotated.width - width) // 2
    top = (rotated.height - height) // 2
    cropped = rotated.crop((left, top, left + width, top + height))

    return cropped


def add_logo_overlay(base_image, logo_path, logo_scale=0.14, logo_opacity=160):
    if not logo_path:
        return base_image

    logo_file = Path(logo_path)
    if not logo_file.exists():
        print(f"[WARN] Logo introuvable: {logo_path}")
        return base_image

    base = base_image.copy().convert("RGBA")
    width, height = base.size

    logo = Image.open(logo_file).convert("RGBA")
    target_w = max(60, int(width * logo_scale))
    ratio = target_w / logo.width
    target_h = max(1, int(logo.height * ratio))
    logo = logo.resize((target_w, target_h), Image.Resampling.LANCZOS)
    logo = apply_alpha_to_rgba(logo, logo_opacity)

    margin = max(15, int(width * 0.02))
    positions = [
        (margin, margin),  # haut gauche
        (width - logo.width - margin, margin),  # haut droite
        (margin, height - logo.height - margin),  # bas gauche
        (width - logo.width - margin, height - logo.height - margin),  # bas droite
    ]

    for pos in positions:
        base.alpha_composite(logo, pos)

    return base


def watermark_pil_image(
    pil_image,
    text,
    logo_path=None,
    font_path=None,
    font_size=None,
    color_rgb=(180, 0, 0),
    opacity=55,
    angle=35,
    spacing_x=None,
    spacing_y=None,
    logo_scale=0.14,
    logo_opacity=160,
):
    img = pil_image.convert("RGBA")
    width, height = img.size

    if font_size is None:
        font_size = max(28, int(min(width, height) * 0.06))

    font = load_font(font_path, font_size)

    overlay = create_text_overlay(
        base_size=img.size,
        text=text,
        font=font,
        color_rgb=color_rgb,
        opacity=opacity,
        angle=angle,
        spacing_x=spacing_x,
        spacing_y=spacing_y,
    )

    out = Image.alpha_composite(img, overlay)

    if logo_path:
        out = add_logo_overlay(
            out,
            logo_path=logo_path,
            logo_scale=logo_scale,
            logo_opacity=logo_opacity,
        )

    return out


def output_path_for(source_path, output_dir=None):
    source_path = Path(source_path)
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / f"{source_path.stem}_watermarked{source_path.suffix}"
    return source_path.with_name(f"{source_path.stem}_watermarked{source_path.suffix}")


def process_image_file(file_path, args, color_rgb, font_path):
    src = Path(file_path)
    dst = output_path_for(src, args.output_dir)

    img = Image.open(src)
    out = watermark_pil_image(
        pil_image=img,
        text=args.text,
        logo_path=args.logo,
        font_path=font_path,
        font_size=args.font_size,
        color_rgb=color_rgb,
        opacity=args.opacity,
        angle=args.angle,
        spacing_x=args.spacing_x,
        spacing_y=args.spacing_y,
        logo_scale=args.logo_scale,
        logo_opacity=args.logo_opacity,
    )

    if src.suffix.lower() in {".jpg", ".jpeg"}:
        out.convert("RGB").save(dst, quality=95)
    else:
        out.save(dst)

    print(f"[OK] Image filigranée : {dst}")


def process_pdf_file(file_path, args, color_rgb, font_path):
    """
    Version simple et robuste :
    - rend chaque page en image à la résolution choisie
    - applique le filigrane avec PIL
    - reconstruit un PDF

    Note honnête : cela rasterise les pages du PDF.
    """
    src = Path(file_path)
    dst = output_path_for(src, args.output_dir)

    doc = fitz.open(src)
    out_doc = fitz.open()

    zoom = args.dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    for page_index, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        watermarked = watermark_pil_image(
            pil_image=img,
            text=args.text,
            logo_path=args.logo,
            font_path=font_path,
            font_size=args.font_size,
            color_rgb=color_rgb,
            opacity=args.opacity,
            angle=args.angle,
            spacing_x=args.spacing_x,
            spacing_y=args.spacing_y,
            logo_scale=args.logo_scale,
            logo_opacity=args.logo_opacity,
        ).convert("RGB")

        buffer = BytesIO()
        watermarked.save(buffer, format="PNG")
        buffer.seek(0)

        rect = fitz.Rect(0, 0, pix.width, pix.height)
        new_page = out_doc.new_page(width=pix.width, height=pix.height)
        new_page.insert_image(rect, stream=buffer.getvalue())

        print(f"[OK] PDF page {page_index}/{len(doc)} traitée")

    out_doc.save(dst)
    out_doc.close()
    doc.close()

    print(f"[OK] PDF filigrané : {dst}")


def list_files_to_process(input_path, recursive=False):
    p = Path(input_path)

    if not p.exists():
        raise FileNotFoundError(f"Chemin introuvable : {input_path}")

    if p.is_file():
        if p.suffix.lower() in SUPPORTED_EXTENSIONS:
            return [p]
        raise ValueError(f"Type de fichier non supporté : {p.suffix}")

    pattern = "**/*" if recursive else "*"
    files = [
        f
        for f in p.glob(pattern)
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    return sorted(files)


def main():
    args = parse_args()

    try:
        color_rgb = parse_rgb(args.color)
    except ValueError as exc:
        print(f"[ERREUR] {exc}")
        sys.exit(1)

    args.opacity = clamp(args.opacity, 0, 255)
    args.logo_opacity = clamp(args.logo_opacity, 0, 255)

    font_path = find_default_font(args.font_path)
    if font_path:
        print(f"[INFO] Police utilisée : {font_path}")
    else:
        print(
            "[WARN] Aucune police TTF/OTF trouvée. Fallback sur police par défaut PIL."
        )

    try:
        files = list_files_to_process(args.input, recursive=args.recursive)
    except Exception as exc:
        print(f"[ERREUR] {exc}")
        sys.exit(1)

    if not files:
        print("[INFO] Aucun fichier supporté trouvé.")
        sys.exit(0)

    for file_path in files:
        try:
            suffix = file_path.suffix.lower()
            if suffix in {".jpg", ".jpeg", ".png"}:
                process_image_file(file_path, args, color_rgb, font_path)
            elif suffix == ".pdf":
                process_pdf_file(file_path, args, color_rgb, font_path)
        except Exception as exc:
            print(f"[ERREUR] {file_path} : {exc}")

    print("[TERMINE]")


if __name__ == "__main__":
    main()
