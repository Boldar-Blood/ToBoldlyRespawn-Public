"""Startup branding asset preparation and Panda3D window branding hooks."""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from panda3d.core import Filename, loadPrcFileData


GAME_WINDOW_TITLE = "To Boldly Respawn: A Co-Op Space Disaster"


class StartupBrandingAssets(NamedTuple):
    """Generated startup branding paths."""

    title_banner: Path
    splash_image: Path
    icon_png: Path
    icon_ico: Path


def data_dir() -> Path:
    """Return the repository/package data directory."""
    return Path(__file__).resolve().parents[2] / "data"


def _normalize_transparent_pixels(image):
    image = image.convert("RGBA")
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = pixels[x, y]
            if a == 0 and (r, g, b) != (0, 0, 0):
                pixels[x, y] = (0, 0, 0, 0)
    return image


def _save_png(image, path: Path) -> None:
    image = _normalize_transparent_pixels(image)
    image.save(path, format="PNG", optimize=True, compress_level=9)


def resolve_title_logo_source(target_dir: Path | None = None) -> Path:
    """Resolve the canonical title logo source, prioritizing curated assets."""
    # 1. Check target_dir / "sprites/title/title_banner.png" if target_dir is provided
    if target_dir is not None:
        target_dir = Path(target_dir)
        curated_target = target_dir / "sprites" / "title" / "title_banner.png"
        if curated_target.exists():
            return curated_target

    # 2. Check data_dir() / "sprites/title/title_banner.png"
    curated_data = data_dir() / "sprites" / "title" / "title_banner.png"
    if curated_data.exists():
        return curated_data

    # 3. Check target_dir / "title_banner.png" if target_dir is provided
    if target_dir is not None:
        fallback_target = target_dir / "title_banner.png"
        if fallback_target.exists():
            return fallback_target

    # 4. Check data_dir() / "title_banner.png"
    fallback_data = data_dir() / "title_banner.png"
    if fallback_data.exists():
        return fallback_data

    # 5. Otherwise, trigger asset generation as final fallback
    from space_demo.core.procedural_gui import generate_gui_assets
    generate_gui_assets()

    if fallback_data.exists():
        return fallback_data

    return fallback_data


def _make_icon_from_title(title_banner: Path, icon_png: Path, icon_ico: Path) -> None:
    """Create square window/package icons derived from the main-menu title logo."""
    from PIL import Image, ImageDraw

    source = Image.open(title_banner).convert("RGBA")
    icon = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)

    # Dark rounded plate so the wide title logo remains visible at smaller sizes.
    draw.rounded_rectangle(
        [(22, 22), (490, 490)],
        radius=88,
        fill=(2, 8, 20, 255),
        outline=(51, 153, 255, 255),
        width=12,
    )
    draw.rounded_rectangle(
        [(52, 52), (460, 460)],
        radius=66,
        outline=(255, 153, 51, 220),
        width=6,
    )

    fitted = source.resize((448, 168), resample=Image.Resampling.LANCZOS)
    icon.alpha_composite(fitted, ((512 - fitted.width) // 2, 172))

    _save_png(icon, icon_png)
    icon.save(icon_ico, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])


def _make_startup_splash(title_banner: Path, splash_image: Path) -> None:
    """Create a branded loading image shown by Panda before the full UI is ready."""
    from PIL import Image, ImageDraw, ImageFont

    banner = Image.open(title_banner).convert("RGBA")
    splash = Image.new("RGBA", (1280, 720), (8, 16, 32, 255))
    draw = ImageDraw.Draw(splash)

    # Subtle sci-fi frame and star points.
    draw.rectangle([(0, 0), (1279, 719)], outline=(51, 153, 255, 220), width=4)
    draw.rectangle([(30, 30), (1250, 690)], outline=(255, 153, 51, 150), width=2)
    for i in range(72):
        x = (i * 173) % 1210 + 35
        y = (i * 97) % 620 + 50
        alpha = 70 + (i * 37) % 130
        splash.putpixel((x, y), (180, 220, 255, alpha))

    fitted = banner.resize((900, 338), resample=Image.Resampling.LANCZOS)
    splash.alpha_composite(fitted, ((1280 - fitted.width) // 2, 166))

    try:
        font = ImageFont.truetype("C:\\Windows\\Fonts\\consolab.ttf", 32)
    except Exception:
        font = ImageFont.load_default()
    draw.text((640, 560), "INITIALIZING RETREAT PROTOCOLS...", font=font, anchor="mm", fill=(210, 240, 255, 230))

    _save_png(splash, splash_image)


def prepare_startup_branding_assets(target_dir: Path | None = None) -> StartupBrandingAssets:
    """Generate title-derived splash and icon assets before Panda opens a window."""
    target_dir = Path(target_dir) if target_dir is not None else data_dir()
    title_banner = resolve_title_logo_source(target_dir)
    splash_image = target_dir / "startup_splash.png"
    icon_png = target_dir / "game_icon.png"
    icon_ico = target_dir / "game_icon.ico"

    _make_startup_splash(title_banner, splash_image)
    _make_icon_from_title(title_banner, icon_png, icon_ico)

    return StartupBrandingAssets(
        title_banner=title_banner,
        splash_image=splash_image,
        icon_png=icon_png,
        icon_ico=icon_ico,
    )


def _prc_path(path: Path) -> str:
    return Filename.fromOsSpecific(str(path)).getFullpath()


def build_startup_prc_config(assets: StartupBrandingAssets) -> str:
    """Build the startup configuration string for loadPrcFileData."""
    icon_path = assets.icon_ico if assets.icon_ico.exists() else assets.icon_png
    lines = [
        f"window-title {GAME_WINDOW_TITLE}",
        f"icon-filename {_prc_path(icon_path)}",
        "splash-window #t",
        f"splash-filename {_prc_path(assets.splash_image)}",
    ]
    return "\n".join(lines)


def apply_startup_branding(headless: bool = False) -> StartupBrandingAssets | None:
    """Configure Panda3D startup splash and icon before ShowBase is constructed."""
    if headless:
        return None

    assets = prepare_startup_branding_assets()
    config_str = build_startup_prc_config(assets)
    loadPrcFileData("startup-branding", config_str)
    return assets
