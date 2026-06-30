"""Supplemental procedural asset generation for To Boldly Respawn.

The generated images are original vector-style sprites and UI panels. They avoid
protected franchise logos, names, silhouettes, and trade dress, and they do not
make Blender a runtime dependency.
"""

from __future__ import annotations

from pathlib import Path
import math
import shutil
from typing import Iterable

# PIL imports are done lazily inside functions to avoid module import-time dependency.


GENERATED_ASSET_NAMES = {
    "title_banner.png",
    "player_hull_100.png",
    "player_hull_75.png",
    "player_hull_50.png",
    "player_hull_25.png",
    "player_hull_critical.png",
    "enemy_drone.png",
    "enemy_speeder.png",
    "enemy_zigzag.png",
    "enemy_frigate.png",
    "enemy_missile_boat.png",
    "enemy_mine.png",
    "dreadnought_phase_1.png",
    "dreadnought_phase_2.png",
    "dreadnought_phase_3.png",
    "dreadnought_destroyed.png",
    "icon_player_mini.png",
    "icon_dreadnought_mini.png",
    "ui_pursuit_gauge.png",
    "ui_panel_glass.png",
    "ui_panel_card.png",
    "vfx_muzzle_flash.png",
    "vfx_explosion_core.png",
    "vfx_explosion_ring.png",
    "vfx_smoke_puff.png",
    "vfx_spark.png",
    "vfx_shockwave_orange.png",
    "vfx_shockwave_cyan.png",
}


def candidate_data_dirs() -> list[Path]:
    """Return in-repository data dirs used by source and packaged runs."""
    module_dir = Path(__file__).resolve().parent
    repo_root = module_dir.parents[2]
    candidates = [repo_root / "data", repo_root / "src" / "data"]
    return list(dict.fromkeys(candidates))


def choose_primary_data_dir() -> Path:
    """Prefer the directory containing existing hand-authored base assets."""
    for path in candidate_data_dirs():
        if (path / "player_skin.png").exists() or (path / "space_background.png").exists():
            return path
    return candidate_data_dirs()[0]


def _resample_filter():
    from PIL import Image
    try:
        return Image.Resampling.LANCZOS
    except AttributeError:  # pragma: no cover - older Pillow compatibility.
        return Image.LANCZOS


def _font_candidates() -> Iterable[Path]:
    """Yield cross-platform bold font candidates without bundling fonts."""
    for raw in (
        r"C:\Windows\Fonts\bahnschrift.ttf",
        r"C:\Windows\Fonts\gadugib.ttf",
        r"C:\Windows\Fonts\consolab.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ):
        path = Path(raw)
        if path.exists():
            yield path


def _load_font(size: int) -> "ImageFont.ImageFont":
    from PIL import ImageFont
    for path in _font_candidates():
        try:
            return ImageFont.truetype(str(path), size)
        except OSError:
            continue
    return ImageFont.load_default()


def _save_downsampled(img: "Image.Image", path: Path, size: tuple[int, int]) -> None:
    from PIL import Image
    path.parent.mkdir(parents=True, exist_ok=True)
    img.resize(size, _resample_filter()).save(path, "PNG")


def generate_title_banner(data_dir: Path) -> None:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    """Generate a readable title/subtitle banner with cross-platform fonts."""
    size = (4096, 1536)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle((80, 80, 4016, 1456), radius=90, outline=(40, 190, 255, 230), width=18)
    draw.rounded_rectangle((180, 180, 3916, 1356), radius=60, outline=(255, 160, 45, 180), width=10)
    for x_pos in (260, 3420):
        draw.rounded_rectangle((x_pos, 230, x_pos + 410, 360), radius=48, fill=(30, 150, 230, 230))
        draw.rounded_rectangle((x_pos, 1176, x_pos + 410, 1306), radius=48, fill=(255, 150, 45, 230))
    for x_pos in range(760, 3340, 260):
        alpha = 70 + (x_pos // 260 % 2) * 50
        draw.line((x_pos, 220, x_pos + 120, 220), fill=(120, 230, 255, alpha), width=10)
        draw.line((x_pos, 1316, x_pos + 120, 1316), fill=(255, 190, 70, alpha), width=10)

    title_font = _load_font(340)
    subtitle_font = _load_font(155)
    title = "TO BOLDLY RESPAWN"
    subtitle = "A CO-OP SPACE DISASTER"

    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.text((2048, 610), title, font=title_font, fill=(0, 190, 255, 190), anchor="mm")
    glow_draw.text((2048, 1000), subtitle, font=subtitle_font, fill=(255, 160, 55, 190), anchor="mm")
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(radius=32)))

    draw.text((2048, 610), title, font=title_font, fill=(238, 250, 255, 255), anchor="mm")
    draw.text((2048, 1000), subtitle, font=subtitle_font, fill=(255, 205, 80, 255), anchor="mm")
    draw.text((2048, 1230), "procedural demo build", font=_load_font(64), fill=(130, 190, 220, 180), anchor="mm")
    _save_downsampled(img, data_dir / "title_banner.png", (1024, 384))


def _draw_ship(draw: ImageDraw.ImageDraw, points, fill, outline, width=10) -> None:
    draw.polygon(points, fill=fill, outline=outline)
    draw.line(points + [points[0]], fill=outline, width=width)


def generate_player_damage_sprites(data_dir: Path) -> None:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    """Generate simple hull-state sprites until curated production art is supplied."""
    damage_specs = [
        ("player_hull_100.png", 0, (70, 210, 255, 245)),
        ("player_hull_75.png", 1, (90, 230, 190, 245)),
        ("player_hull_50.png", 2, (255, 210, 80, 245)),
        ("player_hull_25.png", 3, (255, 130, 40, 245)),
        ("player_hull_critical.png", 4, (255, 55, 55, 250)),
    ]
    for filename, damage_level, accent in damage_specs:
        img = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
        glow = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.ellipse((140, 80, 884, 900), fill=(40, 185, 255, 38))
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(radius=38)))
        draw = ImageDraw.Draw(img)
        hull = (38, 52, 68, 248)
        edge = (210, 236, 255, 245)
        _draw_ship(draw, [(512, 90), (760, 630), (610, 820), (512, 735), (414, 820), (264, 630)], hull, edge, 12)
        draw.line((512, 135, 512, 705), fill=accent, width=22)
        draw.line((372, 540, 652, 540), fill=accent, width=20)
        draw.ellipse((444, 340, 580, 476), fill=(5, 22, 42, 250), outline=accent, width=9)
        for idx in range(damage_level):
            x = 340 + idx * 90
            draw.line((x, 640, x + 80, 720), fill=(255, 80, 50, 230), width=12)
            draw.line((x + 10, 720, x + 90, 650), fill=(255, 200, 85, 180), width=6)
        _save_downsampled(img.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=2)), data_dir / filename, (512, 512))


def generate_enemy_sprite(data_dir: Path, filename: str, kind: str) -> None:
    """Generate an original top-down enemy sprite variant."""
    img = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    glow = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((130, 130, 894, 894), fill=(40, 120, 255, 32))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(radius=34)))
    draw = ImageDraw.Draw(img)
    hull = (34, 38, 52, 245)
    edge = (170, 190, 220, 245)

    if kind == "drone":
        accent = (50, 210, 255, 235)
        _draw_ship(draw, [(512, 120), (790, 700), (512, 590), (234, 700)], hull, edge, 12)
        draw.line((350, 520, 674, 520), fill=accent, width=28)
        draw.ellipse((440, 330, 584, 474), fill=(15, 35, 65, 255), outline=accent, width=10)
    elif kind == "speeder":
        accent = (255, 210, 70, 240)
        _draw_ship(draw, [(512, 80), (710, 760), (512, 690), (314, 760)], hull, edge, 12)
        draw.line((432, 270, 512, 630, 592, 270), fill=accent, width=22)
        draw.rectangle((462, 120, 562, 210), fill=(255, 85, 35, 235))
    elif kind == "zigzag":
        accent = (210, 90, 255, 235)
        pts = [(512, 115), (820, 540), (620, 520), (690, 785), (512, 665), (334, 785), (404, 520), (204, 540)]
        _draw_ship(draw, pts, hull, edge, 10)
        draw.line((310, 540, 512, 350, 714, 540), fill=accent, width=24)
    elif kind == "frigate":
        accent = (70, 245, 130, 235)
        _draw_ship(draw, [(512, 110), (850, 300), (746, 760), (512, 840), (278, 760), (174, 300)], hull, edge, 12)
        for x_pos in (330, 512, 694):
            draw.rounded_rectangle((x_pos - 34, 260, x_pos + 34, 720), radius=22, fill=(20, 65, 45, 245), outline=accent, width=8)
    elif kind == "missile_boat":
        accent = (255, 165, 50, 240)
        _draw_ship(draw, [(512, 100), (820, 610), (650, 820), (512, 720), (374, 820), (204, 610)], hull, edge, 12)
        for x_pos in (365, 512, 659):
            draw.rounded_rectangle((x_pos - 42, 270, x_pos + 42, 620), radius=28, fill=(65, 35, 20, 245), outline=accent, width=8)
    elif kind == "mine":
        accent = (255, 70, 35, 245)
        draw.ellipse((290, 290, 734, 734), fill=(45, 22, 22, 245), outline=accent, width=18)
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            cx = 512 + math.cos(rad) * 300
            cy = 512 + math.sin(rad) * 300
            draw.line((512, 512, cx, cy), fill=accent, width=18)
            draw.ellipse((cx - 36, cy - 36, cx + 36, cy + 36), fill=accent)
        draw.ellipse((415, 415, 609, 609), fill=(90, 18, 12, 245), outline=(255, 190, 90, 245), width=10)

    _save_downsampled(img.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=2)), data_dir / filename, (512, 512))


def generate_dreadnought_sprites(data_dir: Path) -> None:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    """Generate multi-phase dreadnought fallback sprites."""
    specs = [
        ("dreadnought_phase_1.png", (255, 160, 60, 240), 0),
        ("dreadnought_phase_2.png", (255, 95, 55, 245), 1),
        ("dreadnought_phase_3.png", (255, 45, 80, 250), 2),
        ("dreadnought_destroyed.png", (155, 160, 170, 180), 3),
    ]
    for filename, accent, damage_level in specs:
        img = Image.new("RGBA", (1536, 1024), (0, 0, 0, 0))
        glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.ellipse((190, 100, 1346, 900), fill=(255, 110, 40, 34))
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(radius=42)))
        draw = ImageDraw.Draw(img)
        hull = (42, 44, 55, 248)
        edge = (225, 205, 180, 245)
        body = [(768, 100), (1260, 390), (1110, 820), (768, 690), (426, 820), (276, 390)]
        _draw_ship(draw, body, hull, edge, 14)
        draw.rounded_rectangle((555, 285, 981, 590), radius=54, fill=(18, 22, 34, 245), outline=accent, width=12)
        draw.line((390, 420, 1146, 420), fill=accent, width=20)
        draw.line((510, 620, 1026, 620), fill=(accent[0], accent[1], accent[2], 170), width=16)
        for idx in range(damage_level):
            x = 470 + idx * 175
            draw.line((x, 300, x + 210, 700), fill=(255, 70, 45, 230), width=18)
            draw.line((x + 40, 700, x + 220, 340), fill=(255, 210, 80, 170), width=8)
        if damage_level >= 3:
            draw.rectangle((500, 430, 1040, 530), fill=(0, 0, 0, 120))
        _save_downsampled(img.filter(ImageFilter.UnsharpMask(radius=1, percent=130, threshold=2)), data_dir / filename, (768, 512))


def generate_ui_panels(data_dir: Path) -> None:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    """Generate reusable original panel art for future image-backed panels."""
    for filename, color in (
        ("ui_panel_glass.png", (40, 185, 255, 210)),
        ("ui_panel_card.png", (255, 160, 55, 210)),
    ):
        img = Image.new("RGBA", (1024, 512), (0, 0, 0, 0))
        glow = Image.new("RGBA", (1024, 512), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.rounded_rectangle((40, 40, 984, 472), radius=52, outline=color, width=36)
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(radius=18)))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((56, 56, 968, 456), radius=46, fill=(5, 12, 28, 190), outline=color, width=8)
        draw.line((120, 116, 904, 116), fill=(color[0], color[1], color[2], 110), width=5)
        draw.line((120, 396, 904, 396), fill=(color[0], color[1], color[2], 70), width=4)
        _save_downsampled(img, data_dir / filename, (512, 256))


def generate_pursuit_gauge_and_icons(data_dir: Path) -> None:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    """Generate pursuit gauge and mini marker fallbacks."""
    gauge = Image.new("RGBA", (256, 1024), (0, 0, 0, 0))
    glow = Image.new("RGBA", gauge.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.rounded_rectangle((84, 52, 172, 972), radius=34, outline=(255, 170, 45, 180), width=22)
    gauge.alpha_composite(glow.filter(ImageFilter.GaussianBlur(radius=14)))
    draw = ImageDraw.Draw(gauge)
    draw.rounded_rectangle((96, 64, 160, 960), radius=28, fill=(4, 12, 24, 210), outline=(255, 190, 80, 230), width=6)
    for idx, z in enumerate(range(122, 930, 92)):
        width = 40 if idx % 2 == 0 else 26
        draw.line((128 - width // 2, z, 128 + width // 2, z), fill=(130, 230, 255, 150), width=5)
    _save_downsampled(gauge, data_dir / "ui_pursuit_gauge.png", (128, 512))

    for filename, color, points in (
        ("icon_player_mini.png", (70, 220, 255, 245), [(128, 20), (212, 202), (128, 168), (44, 202)]),
        ("icon_dreadnought_mini.png", (255, 130, 55, 245), [(128, 28), (230, 105), (204, 216), (128, 184), (52, 216), (26, 105)]),
    ):
        icon = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        icon_glow = Image.new("RGBA", icon.size, (0, 0, 0, 0))
        icon_draw = ImageDraw.Draw(icon_glow)
        icon_draw.ellipse((36, 28, 220, 228), fill=(color[0], color[1], color[2], 55))
        icon.alpha_composite(icon_glow.filter(ImageFilter.GaussianBlur(radius=14)))
        draw = ImageDraw.Draw(icon)
        _draw_ship(draw, points, (30, 34, 46, 245), (225, 235, 245, 245), 5)
        draw.line((70, 128, 186, 128), fill=color, width=7)
        _save_downsampled(icon, data_dir / filename, (128, 128))


def generate_vfx_sprites(data_dir: Path) -> None:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    """Generate transparent VFX sprites for runtime fallback effects."""
    def radial(filename: str, color: tuple[int, int, int], rings: int = 4, size: int = 512) -> None:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        center = size // 2
        for idx in range(rings, 0, -1):
            radius = int(center * idx / rings * 0.92)
            alpha = int(190 / idx)
            draw.ellipse((center - radius, center - radius, center + radius, center + radius), outline=(*color, alpha), width=max(4, size // 42))
        draw.ellipse((center - size // 9, center - size // 9, center + size // 9, center + size // 9), fill=(*color, 220))
        img = img.filter(ImageFilter.GaussianBlur(radius=2))
        img.save(data_dir / filename, "PNG")

    radial("vfx_explosion_ring.png", (255, 135, 45), rings=5)
    radial("vfx_shockwave_orange.png", (255, 150, 45), rings=3)
    radial("vfx_shockwave_cyan.png", (50, 220, 255), rings=3)

    for filename, color, blur in (
        ("vfx_explosion_core.png", (255, 185, 65), 8),
        ("vfx_muzzle_flash.png", (80, 230, 255), 5),
        ("vfx_spark.png", (255, 235, 120), 3),
        ("vfx_smoke_puff.png", (110, 125, 140), 12),
    ):
        img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            length = 100 if filename != "vfx_smoke_puff.png" else 62
            x2 = 128 + math.cos(rad) * length
            y2 = 128 + math.sin(rad) * length
            draw.line((128, 128, x2, y2), fill=(*color, 150), width=12)
        draw.ellipse((58, 58, 198, 198), fill=(*color, 180))
        img.filter(ImageFilter.GaussianBlur(radius=blur)).save(data_dir / filename, "PNG")


def mirror_generated_assets(primary_dir: Path) -> None:
    """Copy generated assets to secondary in-repo data dirs only."""
    for target_dir in candidate_data_dirs():
        if target_dir == primary_dir:
            continue
        target_dir.mkdir(parents=True, exist_ok=True)
        for filename in GENERATED_ASSET_NAMES:
            source = primary_dir / filename
            if source.exists():
                shutil.copy2(source, target_dir / filename)


def generate_extra_assets() -> Path:
    """Generate supplemental Pillow assets and mirror them for package parity."""
    data_dir = choose_primary_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if all files in GENERATED_ASSET_NAMES exist in data_dir
    all_exist = True
    for filename in GENERATED_ASSET_NAMES:
        if not (data_dir / filename).exists():
            all_exist = False
            break
    if all_exist:
        return data_dir

    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageFont
    except ImportError as exc:
        print(f"[GUI Asset] Warning: Pillow is not installed. Skipping extra asset generation: {exc}")
        return data_dir

    generate_title_banner(data_dir)
    generate_player_damage_sprites(data_dir)
    generate_enemy_sprite(data_dir, "enemy_drone.png", "drone")
    generate_enemy_sprite(data_dir, "enemy_speeder.png", "speeder")
    generate_enemy_sprite(data_dir, "enemy_zigzag.png", "zigzag")
    generate_enemy_sprite(data_dir, "enemy_frigate.png", "frigate")
    generate_enemy_sprite(data_dir, "enemy_missile_boat.png", "missile_boat")
    generate_enemy_sprite(data_dir, "enemy_mine.png", "mine")
    generate_dreadnought_sprites(data_dir)
    generate_ui_panels(data_dir)
    generate_pursuit_gauge_and_icons(data_dir)
    generate_vfx_sprites(data_dir)
    mirror_generated_assets(data_dir)
    return data_dir


if __name__ == "__main__":
    generate_extra_assets()
