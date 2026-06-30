# Procedural GUI Asset Generator - To Boldly Respawn

import os


def _save_png(image: "Image.Image", path: str) -> None:
    """Save a PNG with transparent pixels normalized to transparent black.

    This prevents hidden RGB values under alpha=0 from creating light fringes
    during texture filtering or scaling.
    """
    from PIL import Image
    image = image.convert("RGBA")
    pixels = image.load()

    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = pixels[x, y]
            if a == 0 and (r, g, b) != (0, 0, 0):
                pixels[x, y] = (0, 0, 0, 0)

    image.save(path, format="PNG", optimize=True, compress_level=9)

def generate_gui_assets():
    """Generate procedural fallback GUI, pickup, shield, and VFX assets."""
    # Resolve the data directory inside the workspace
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))
    
    expected_assets = [
        "pickup_shield.png", "shield_skin.png", "pickup_bomb.png", "pickup_magnet.png",
        "pickup_intern.png", "pickup_missile.png", "vfx_muzzle_flash.png", "vfx_explosion_core.png",
        "vfx_explosion_ring.png", "vfx_smoke_puff.png", "vfx_spark.png", "vfx_shockwave_orange.png",
        "vfx_shockwave_cyan.png", "title_banner.png", "icon_player_mini.png", "icon_dreadnought_mini.png",
        "ui_pursuit_gauge.png", "dreadnought_phase_1.png", "dreadnought_phase_2.png", "dreadnought_phase_3.png",
        "dreadnought_destroyed.png", "player_hull_100.png", "player_hull_75.png", "player_hull_50.png",
        "player_hull_25.png", "player_hull_critical.png"
    ]
    all_exist = True
    for asset in expected_assets:
        if not os.path.exists(os.path.join(data_dir, asset)):
            all_exist = False
            break
    if all_exist:
        return

    try:
        from PIL import Image, ImageDraw, ImageFilter
    except ImportError as exc:
        print(f"[GUI Asset] Warning: Pillow is not installed. Skipping procedural GUI asset generation: {exc}")
        return

    os.makedirs(data_dir, exist_ok=True)

    # Determine standard LANCZOS filter compatibility across Pillow versions
    try:
        resample_filter = Image.Resampling.LANCZOS
    except AttributeError:
        resample_filter = Image.LANCZOS

    # DirectGUI buttons/sliders are styled directly at runtime. The generated
    # GUI fallback pass starts with gameplay pickup/indicator textures.

    # Liability Waiver Shield Pickup Icon (512x512, supersampled at 2048x2048)
    pickup_shield_path = os.path.join(data_dir, "pickup_shield.png")
    img_pu_large = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    
    # Outer glow layer
    glow_pu = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    glow_draw_pu = ImageDraw.Draw(glow_pu)
    glow_draw_pu.ellipse([(200, 200), (1848, 1848)], fill=(0, 180, 255, 90))
    glow_pu = glow_pu.filter(ImageFilter.GaussianBlur(radius=40))
    img_pu_large.paste(glow_pu, (0, 0), glow_pu)
    
    # Crisp vector details
    draw_pu = ImageDraw.Draw(img_pu_large)
    # Draw dark backing circle
    draw_pu.ellipse([(350, 350), (1698, 1698)], fill=(10, 30, 50, 180), outline=(0, 200, 255, 255), width=24)
    # Draw concentric inner ring
    draw_pu.ellipse([(450, 450), (1598, 1598)], outline=(0, 120, 255, 255), width=12)
    # Draw high-tech shield shape
    shield_polygon = [
        (600, 700),
        (1024, 580),
        (1448, 700),
        (1400, 1150),
        (1024, 1550),
        (648, 1150)
    ]
    draw_pu.polygon(shield_polygon, fill=(0, 200, 255, 200), outline=(200, 255, 255, 255), width=20)
    # Draw diagonal visual highlight
    draw_pu.line([(720, 950), (1328, 950)], fill=(255, 255, 255, 120), width=16)
    
    img_pu = img_pu_large.resize((512, 512), resample=resample_filter)
    _save_png(img_pu, pickup_shield_path)
    print(f"[GUI Asset] Generated premium shield pickup icon (Anti-Aliased): {pickup_shield_path}")

    # Liability Waiver Shield Skin/Bubble (1024x1024, supersampled at 4096x4096)
    shield_skin_path = os.path.join(data_dir, "shield_skin.png")
    img_ss_large = Image.new("RGBA", (4096, 4096), (0, 0, 0, 0))
    
    # Outer glow ring layer
    glow_ss = Image.new("RGBA", (4096, 4096), (0, 0, 0, 0))
    glow_draw_ss = ImageDraw.Draw(glow_ss)
    glow_draw_ss.ellipse([(400, 400), (3696, 3696)], outline=(0, 180, 255, 120), width=360)
    glow_ss = glow_ss.filter(ImageFilter.GaussianBlur(radius=60))
    img_ss_large.paste(glow_ss, (0, 0), glow_ss)
    
    # Crisp sharp vector lines
    draw_ss = ImageDraw.Draw(img_ss_large)
    draw_ss.ellipse([(480, 480), (3616, 3616)], outline=(180, 240, 255, 255), width=64)
    draw_ss.ellipse([(640, 640), (3456, 3456)], outline=(0, 140, 255, 200), width=24)
    draw_ss.ellipse([(360, 360), (3736, 3736)], outline=(0, 120, 255, 180), width=16)
    
    # Cybernetic notches
    draw_ss.rectangle([(2000, 240), (2096, 440)], fill=(180, 240, 255, 255))
    draw_ss.rectangle([(2000, 3656), (2096, 3856)], fill=(180, 240, 255, 255))
    draw_ss.rectangle([(240, 2000), (440, 2096)], fill=(180, 240, 255, 255))
    draw_ss.rectangle([(3656, 2000), (3856, 2096)], fill=(180, 240, 255, 255))
    
    img_ss = img_ss_large.resize((1024, 1024), resample=resample_filter)
    _save_png(img_ss, shield_skin_path)
    print(f"[GUI Asset] Generated premium hollow shield bubble skin (Anti-Aliased): {shield_skin_path}")

    # Executive Decision Bomb Pickup Icon (512x512, supersampled at 2048x2048)
    pickup_bomb_path = os.path.join(data_dir, "pickup_bomb.png")
    img_pb_large = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    
    # Outer glow layer (neon orange / red-orange glow)
    glow_pb = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    glow_draw_pb = ImageDraw.Draw(glow_pb)
    glow_draw_pb.ellipse([(200, 200), (1848, 1848)], fill=(255, 120, 0, 90))
    glow_pb = glow_pb.filter(ImageFilter.GaussianBlur(radius=40))
    img_pb_large.paste(glow_pb, (0, 0), glow_pb)
    
    # Crisp vector details
    draw_pb = ImageDraw.Draw(img_pb_large)
    # Draw dark backing circle
    draw_pb.ellipse([(350, 350), (1698, 1698)], fill=(50, 20, 10, 180), outline=(255, 120, 0, 255), width=24)
    # Draw concentric inner ring
    draw_pb.ellipse([(450, 450), (1598, 1598)], outline=(255, 80, 0, 255), width=12)
    
    # Draw high-tech executive folder/briefcase shape
    briefcase_poly = [
        (600, 750),
        (1448, 750),
        (1448, 1400),
        (600, 1400)
    ]
    # Draw briefcase handle
    draw_pb.rounded_rectangle([(850, 600), (1198, 750)], radius=30, outline=(255, 150, 0, 255), width=24)
    # Fill briefcase body
    draw_pb.polygon(briefcase_poly, fill=(255, 120, 0, 200), outline=(255, 200, 100, 255), width=20)
    # Horizontal status bar slash
    draw_pb.line([(700, 1075), (1348, 1075)], fill=(255, 255, 255, 150), width=18)
    
    img_pb = img_pb_large.resize((512, 512), resample=resample_filter)
    _save_png(img_pb, pickup_bomb_path)
    print(f"[GUI Asset] Generated premium bomb pickup icon (Anti-Aliased): {pickup_bomb_path}")

    # Synergy Magnet Pickup Icon (512x512, supersampled at 2048x2048)
    pickup_magnet_path = os.path.join(data_dir, "pickup_magnet.png")
    img_pm_large = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    
    # Outer glow layer (neon violet/purple glow)
    glow_pm = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    glow_draw_pm = ImageDraw.Draw(glow_pm)
    glow_draw_pm.ellipse([(200, 200), (1848, 1848)], fill=(180, 80, 255, 90))
    glow_pm = glow_pm.filter(ImageFilter.GaussianBlur(radius=40))
    img_pm_large.paste(glow_pm, (0, 0), glow_pm)
    
    # Crisp vector details
    draw_pm = ImageDraw.Draw(img_pm_large)
    # Draw dark backing circle
    draw_pm.ellipse([(350, 350), (1698, 1698)], fill=(20, 10, 45, 180), outline=(180, 80, 255, 255), width=24)
    # Draw concentric inner ring
    draw_pm.ellipse([(450, 450), (1598, 1598)], outline=(140, 50, 220, 255), width=12)
    
    # Draw horseshoe U-shaped magnet base
    # Outer curve
    draw_pm.arc([(600, 650), (1448, 1450)], start=0, end=180, fill=(180, 80, 255, 255), width=160)
    # Left arm extending up
    draw_pm.rectangle([(600, 750), (760, 1050)], fill=(180, 80, 255, 255))
    # Right arm extending up
    draw_pm.rectangle([(1288, 750), (1448, 1050)], fill=(180, 80, 255, 255))
    # Draw white contact tips (poles)
    draw_pm.rectangle([(600, 675), (760, 750)], fill=(240, 240, 255, 255))
    draw_pm.rectangle([(1288, 675), (1448, 750)], fill=(240, 240, 255, 255))
    # Subtle spark/consolidation lines between poles
    draw_pm.line([(820, 712), (1228, 712)], fill=(255, 255, 255, 150), width=12)
    
    img_pm = img_pm_large.resize((512, 512), resample=resample_filter)
    _save_png(img_pm, pickup_magnet_path)
    print(f"[GUI Asset] Generated premium magnet pickup icon (Anti-Aliased): {pickup_magnet_path}")

    # Unpaid Intern Pickup Icon (512x512, supersampled at 2048x2048)
    pickup_intern_path = os.path.join(data_dir, "pickup_intern.png")
    img_pi_large = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    
    # Outer glow layer (neon cyan glow)
    glow_pi = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    glow_draw_pi = ImageDraw.Draw(glow_pi)
    glow_draw_pi.ellipse([(200, 200), (1848, 1848)], fill=(40, 200, 255, 90))
    glow_pi = glow_pi.filter(ImageFilter.GaussianBlur(radius=40))
    img_pi_large.paste(glow_pi, (0, 0), glow_pi)
    
    # Crisp vector details
    draw_pi = ImageDraw.Draw(img_pi_large)
    # Draw dark backing circle
    draw_pi.ellipse([(350, 350), (1698, 1698)], fill=(10, 30, 45, 180), outline=(40, 200, 255, 255), width=24)
    # Draw concentric inner ring
    draw_pi.ellipse([(450, 450), (1598, 1598)], outline=(20, 130, 180, 255), width=12)
    
    # Draw coffee cup body
    # Cup bowl: rounded shape in center
    draw_pi.chord([(700, 800), (1348, 1350)], start=0, end=180, fill=(40, 200, 255, 200), outline=(100, 230, 255, 255), width=20)
    # Top rim bar
    draw_pi.rounded_rectangle([(670, 780), (1378, 830)], radius=15, fill=(40, 200, 255, 255), outline=(100, 230, 255, 255), width=10)
    # Cup handle on the right side
    draw_pi.arc([(1250, 880), (1450, 1180)], start=270, end=90, fill=(100, 230, 255, 255), width=24)
    # Steam waves rising up
    draw_pi.arc([(800, 580), (950, 730)], start=180, end=360, fill=(240, 250, 255, 250), width=14)
    draw_pi.arc([(900, 550), (1050, 700)], start=0, end=180, fill=(240, 250, 255, 250), width=14)
    draw_pi.arc([(1050, 580), (1200, 730)], start=180, end=360, fill=(240, 250, 255, 250), width=14)
    
    img_pi = img_pi_large.resize((512, 512), resample=resample_filter)
    _save_png(img_pi, pickup_intern_path)
    print(f"[GUI Asset] Generated premium unpaid intern pickup icon (Anti-Aliased): {pickup_intern_path}")

    # Ammo Canister Pickup Icon (512x512, supersampled at 2048x2048)
    pickup_missile_path = os.path.join(data_dir, "pickup_missile.png")
    img_pm_large = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    
    # Outer glow layer (neon orange / amber glow)
    glow_pm = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    glow_draw_pm = ImageDraw.Draw(glow_pm)
    glow_draw_pm.ellipse([(200, 200), (1848, 1848)], fill=(255, 150, 0, 90))
    glow_pm = glow_pm.filter(ImageFilter.GaussianBlur(radius=40))
    img_pm_large.paste(glow_pm, (0, 0), glow_pm)
    
    # Crisp vector details
    draw_pm = ImageDraw.Draw(img_pm_large)
    # Draw dark backing circle
    draw_pm.ellipse([(350, 350), (1698, 1698)], fill=(40, 20, 5, 180), outline=(255, 150, 0, 255), width=24)
    # Draw concentric inner ring
    draw_pm.ellipse([(450, 450), (1598, 1598)], outline=(200, 100, 0, 255), width=12)
    
    # Draw a stylized cargo box / ammo crate in the center
    # Main outer rectangle
    draw_pm.rounded_rectangle([(650, 650), (1398, 1398)], radius=60, fill=(255, 150, 0, 200), outline=(255, 230, 150, 255), width=20)
    # Draw an X-brace across the cargo box (classic sci-fi crate look!)
    draw_pm.line([(700, 700), (1348, 1348)], fill=(255, 230, 150, 255), width=24)
    draw_pm.line([(1348, 700), (700, 1348)], fill=(255, 230, 150, 255), width=24)
    # Draw center ammo insignia (three small vertical pill bullet shapes inside a small dark backing circle)
    draw_pm.ellipse([(874, 874), (1174, 1174)], fill=(10, 5, 0, 240), outline=(255, 150, 0, 255), width=8)
    draw_pm.rounded_rectangle([(934, 924), (964, 1124)], radius=15, fill=(255, 200, 50, 255))
    draw_pm.rounded_rectangle([(1009, 924), (1039, 1124)], radius=15, fill=(255, 200, 50, 255))
    draw_pm.rounded_rectangle([(1084, 924), (1114, 1124)], radius=15, fill=(255, 200, 50, 255))
    
    img_pm = img_pm_large.resize((512, 512), resample=resample_filter)
    _save_png(img_pm, pickup_missile_path)
    print(f"[GUI Asset] Generated premium ammunition canister pickup icon (Anti-Aliased): {pickup_missile_path}")

    # Premium VFX Textures (Muzzle Flash, Explosion Core/Ring, Sparks, Smoke Puffs, Neon Shockwaves)
    def generate_radial_glow(path, size=256, color=(255, 210, 70, 255), power=2.0):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx = cy = size // 2
        max_r = size // 2
        for r in range(max_r, 0, -1):
            ratio = r / max_r
            alpha = int(color[3] * (1.0 - ratio) ** power)
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(color[0], color[1], color[2], alpha))
        img = img.filter(ImageFilter.GaussianBlur(radius=2))
        _save_png(img, path)
        print(f"[VFX Asset] Generated premium radial glow: {os.path.basename(path)}")

    def generate_ring_glow(path, size=256, color=(255, 120, 20, 255), thickness=0.15):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx = cy = size // 2
        max_r = size // 2
        for r in range(max_r, 0, -1):
            ratio = r / max_r
            dist = abs(ratio - 0.8)
            if dist < thickness:
                alpha = int(color[3] * (1.0 - (dist / thickness)) ** 2)
            else:
                alpha = 0
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(color[0], color[1], color[2], alpha))
        img = img.filter(ImageFilter.GaussianBlur(radius=2))
        _save_png(img, path)
        print(f"[VFX Asset] Generated premium ring glow: {os.path.basename(path)}")

    def generate_spark_diamond(path, size=128, color=(255, 230, 100, 255)):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx = cy = size // 2
        draw.polygon([
            (cx, 8),
            (cx + size // 4, cy),
            (cx, size - 8),
            (cx - size // 4, cy)
        ], fill=color)
        img = img.filter(ImageFilter.GaussianBlur(radius=1))
        _save_png(img, path)
        print(f"[VFX Asset] Generated premium spark diamond: {os.path.basename(path)}")

    generate_radial_glow(os.path.join(data_dir, "vfx_muzzle_flash.png"), color=(255, 230, 100, 255), power=2.5)
    generate_radial_glow(os.path.join(data_dir, "vfx_explosion_core.png"), color=(255, 120, 30, 255), power=1.8)
    generate_ring_glow(os.path.join(data_dir, "vfx_explosion_ring.png"), color=(255, 90, 10, 255))
    generate_radial_glow(os.path.join(data_dir, "vfx_smoke_puff.png"), color=(60, 60, 65, 180), power=1.5)
    generate_spark_diamond(os.path.join(data_dir, "vfx_spark.png"))
    generate_ring_glow(os.path.join(data_dir, "vfx_shockwave_orange.png"), color=(255, 120, 0, 255), thickness=0.08)
    generate_ring_glow(os.path.join(data_dir, "vfx_shockwave_cyan.png"), color=(0, 180, 255, 255), thickness=0.08)

    # Menu Title Banner Image (1024x384, supersampled at 4096x1536)
    banner_path = os.path.join(data_dir, "title_banner.png")
    img_b_large = Image.new("RGBA", (4096, 1536), (0, 0, 0, 0))
    draw_b = ImageDraw.Draw(img_b_large)
    
    # Left retro-cyber bracket
    draw_b.rectangle([(60, 60), (160, 1476)], fill=(51, 153, 255, 255))
    draw_b.rectangle([(160, 60), (460, 160)], fill=(51, 153, 255, 255))
    draw_b.rectangle([(160, 1376), (460, 1476)], fill=(51, 153, 255, 255))
    
    # Right retro-cyber bracket
    draw_b.rectangle([(3936, 60), (4036, 1476)], fill=(255, 153, 51, 255))
    draw_b.rectangle([(3636, 60), (3936, 160)], fill=(255, 153, 51, 255))
    draw_b.rectangle([(3636, 1376), (3936, 1476)], fill=(255, 153, 51, 255))

    # Standard sci-fi font lookup
    from PIL import ImageFont
    font_title = None
    font_sub = None
    font_candidates = [
        "C:\\Windows\\Fonts\\bahnschrift.ttf",
        "C:\\Windows\\Fonts\\gadugib.ttf",
        "C:\\Windows\\Fonts\\ocra.ttf",
        "C:\\Windows\\Fonts\\consolab.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf"
    ]
    for fp in font_candidates:
        if os.path.exists(fp):
            try:
                font_title = ImageFont.truetype(fp, 360)
                font_sub = ImageFont.truetype(fp, 180)
                break
            except Exception:
                pass
                
    if font_title is None:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # Premium Drop Shadow Glow pass
    shadow_img = Image.new("RGBA", (4096, 1536), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_img)
    if font_title and hasattr(shadow_draw, "text"):
        shadow_draw.text((2048, 520), "TO BOLDLY RESPAWN", font=font_title, fill=(0, 180, 255, 200), anchor="mm")
        shadow_draw.text((2048, 1000), "A CO-OP SPACE DISASTER", font=font_sub, fill=(255, 120, 0, 200), anchor="mm")
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=30))
    img_b_large.paste(shadow_img, (0, 0), shadow_img)

    # Crisp sharp vector foreground text
    if font_title and hasattr(draw_b, "text"):
        draw_b.text((2048, 520), "TO BOLDLY RESPAWN", font=font_title, fill=(240, 250, 255, 255), anchor="mm")
        draw_b.text((2048, 1000), "A CO-OP SPACE DISASTER", font=font_sub, fill=(255, 180, 50, 255), anchor="mm")

    img_b = img_b_large.resize((1024, 384), resample=resample_filter)
    _save_png(img_b, banner_path)
    print(f"[GUI Asset] Generated premium aspect-ratio compensated Menu Title Banner: {banner_path}")

    # Mini Telemetry Icons (128x128, supersampled at 512x512)
    # Icon A: Player Mini (Sleek Cyan Neon Chevron)
    icon_player_path = os.path.join(data_dir, "icon_player_mini.png")
    img_ip_large = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    glow_ip = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    glow_draw_ip = ImageDraw.Draw(glow_ip)
    glow_draw_ip.polygon([(256, 64), (432, 416), (256, 336), (80, 416)], fill=(0, 180, 255, 120))
    glow_ip = glow_ip.filter(ImageFilter.GaussianBlur(radius=15))
    img_ip_large.paste(glow_ip, (0, 0), glow_ip)
    
    draw_ip = ImageDraw.Draw(img_ip_large)
    draw_ip.polygon([(256, 80), (416, 400), (256, 320), (96, 400)], fill=(0, 200, 255, 220), outline=(200, 255, 255, 255), width=8)
    img_ip = img_ip_large.resize((128, 128), resample=resample_filter)
    _save_png(img_ip, icon_player_path)
    print(f"[GUI Asset] Generated premium mini player icon: {icon_player_path}")

    # Icon B: Dreadnought Mini (Menacing Red-Orange Neon Arrowhead)
    icon_dread_path = os.path.join(data_dir, "icon_dreadnought_mini.png")
    img_id_large = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    glow_id = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    glow_draw_id = ImageDraw.Draw(glow_id)
    glow_draw_id.polygon([(256, 48), (448, 432), (256, 320), (64, 432)], fill=(255, 40, 0, 120))
    glow_id = glow_id.filter(ImageFilter.GaussianBlur(radius=15))
    img_id_large.paste(glow_id, (0, 0), glow_id)
    
    draw_id = ImageDraw.Draw(img_id_large)
    draw_id.polygon([(256, 64), (432, 416), (256, 304), (80, 416)], fill=(255, 50, 0, 220), outline=(255, 180, 100, 255), width=8)
    draw_id.line([(192, 340), (320, 340)], fill=(255, 200, 100, 255), width=8)
    img_id = img_id_large.resize((128, 128), resample=resample_filter)
    _save_png(img_id, icon_dread_path)
    print(f"[GUI Asset] Generated premium mini dreadnought icon: {icon_dread_path}")

    # Vertical Pursuit Gauge Track (128x512, supersampled at 512x2048)
    gauge_track_path = os.path.join(data_dir, "ui_pursuit_gauge.png")
    img_gt_large = Image.new("RGBA", (512, 2048), (0, 0, 0, 0))
    
    glow_gt = Image.new("RGBA", (512, 2048), (0, 0, 0, 0))
    glow_draw_gt = ImageDraw.Draw(glow_gt)
    glow_draw_gt.rounded_rectangle([(192, 64), (320, 1984)], radius=32, fill=(0, 50, 100, 160), outline=(0, 180, 255, 160), width=32)
    glow_gt = glow_gt.filter(ImageFilter.GaussianBlur(radius=20))
    img_gt_large.paste(glow_gt, (0, 0), glow_gt)
    
    draw_gt = ImageDraw.Draw(img_gt_large)
    draw_gt.rounded_rectangle([(192, 64), (320, 1984)], radius=32, fill=(10, 20, 40, 180), outline=(0, 180, 255, 255), width=12)
    
    for y in range(256, 1900, 256):
        draw_gt.line([(160, y), (192, y)], fill=(0, 180, 255, 255), width=8)
        draw_gt.line([(320, y), (352, y)], fill=(0, 180, 255, 255), width=8)
        draw_gt.line([(224, y), (288, y)], fill=(0, 180, 255, 100), width=6)
        
    img_gt = img_gt_large.resize((128, 512), resample=resample_filter)
    _save_png(img_gt, gauge_track_path)
    print(f"[GUI Asset] Generated premium pursuit gauge track: {gauge_track_path}")

    # Procedural Boss Phase Textures (1024x768)
    def draw_boss_base(draw, img, damage_level=0):
        # Background is transparent
        # Main Wedge Hull Shape pointing DOWNWARD:
        hull_poly = [(512, 700), (896, 150), (640, 200), (512, 100), (384, 200), (128, 150)]
        draw.polygon(hull_poly, fill=(24, 28, 36, 255), outline=(100, 110, 130, 255), width=8)
        
        # Sleek sci-fi panel stripes
        draw.line([(320, 300), (450, 500)], fill=(255, 120, 0, 255), width=10)
        draw.line([(704, 300), (574, 500)], fill=(255, 120, 0, 255), width=10)
        
        # Center bridges/pods
        draw.rounded_rectangle([(448, 150), (576, 280)], radius=24, fill=(40, 48, 64, 255), outline=(255, 180, 0, 255), width=6)
        
        # Glowing Amber horizontal stripes (sensors)
        for y in range(320, 480, 40):
            draw.line([(470, y), (554, y)], fill=(255, 200, 50, 255), width=6)
            
        # Menacing neon thrusters at the top (orange-red exhaust glowing upward)
        draw.rectangle([(256, 110), (320, 150)], fill=(255, 40, 0, 255), outline=(255, 150, 50, 255), width=4)
        draw.rectangle([(704, 110), (768, 150)], fill=(255, 40, 0, 255), outline=(255, 150, 50, 255), width=4)
        draw.rectangle([(480, 70), (544, 100)], fill=(255, 60, 0, 255), outline=(255, 180, 50, 255), width=4)
        
        # Apply progressive visual damage overlays
        if damage_level >= 1:
            # Phase 2 Scorch marks and cracked plating
            draw.line([(150, 160), (300, 300)], fill=(60, 60, 60, 255), width=6)
            draw.line([(850, 160), (700, 300)], fill=(60, 60, 60, 255), width=6)
            draw.ellipse([(200, 200), (280, 280)], fill=(30, 30, 30, 200))
            draw.ellipse([(650, 400), (720, 470)], fill=(30, 30, 30, 200))
            # Left engine malfunctioning (offline dark grey)
            draw.rectangle([(256, 110), (320, 150)], fill=(50, 50, 50, 255), outline=(100, 100, 100, 255), width=4)
            
        if damage_level >= 2:
            # Phase 3 Exposed reactor core and structural failures
            draw.ellipse([(140, 140), (220, 220)], fill=(0, 0, 0, 0)) # wing hole!
            draw.line([(480, 220), (512, 600)], fill=(255, 0, 50, 255), width=8)
            draw.line([(320, 300), (512, 400)], fill=(255, 0, 50, 255), width=8)
            # Reactor leak core: glowing magenta circle in the center!
            draw.ellipse([(462, 332), (562, 432)], fill=(255, 0, 180, 220), outline=(255, 150, 255, 255), width=6)
            # Right engine also malfunctioning (offline dark grey)
            draw.rectangle([(704, 110), (768, 150)], fill=(50, 50, 50, 255), outline=(100, 100, 100, 255), width=4)

        if damage_level >= 3:
            # Completely destroyed state
            draw.rectangle([(0, 0), (1024, 768)], fill=(15, 15, 15, 180))
            draw.line([(100, 100), (924, 668)], fill=(255, 0, 0, 150), width=16)
            draw.line([(100, 668), (924, 100)], fill=(255, 0, 0, 150), width=16)
            # Offline center engine
            draw.rectangle([(480, 70), (544, 100)], fill=(30, 30, 30, 255), outline=(60, 60, 60, 255), width=4)

    # Save Phase 1 Image
    img_p1 = Image.new("RGBA", (1024, 768), (0, 0, 0, 0))
    draw_boss_base(ImageDraw.Draw(img_p1), img_p1, damage_level=0)
    p1_path = os.path.join(data_dir, "dreadnought_phase_1.png")
    _save_png(img_p1, p1_path)
    print(f"[GUI Asset] Generated premium boss phase 1 texture: {p1_path}")

    # Save Phase 2 Image
    img_p2 = Image.new("RGBA", (1024, 768), (0, 0, 0, 0))
    draw_boss_base(ImageDraw.Draw(img_p2), img_p2, damage_level=1)
    p2_path = os.path.join(data_dir, "dreadnought_phase_2.png")
    _save_png(img_p2, p2_path)
    print(f"[GUI Asset] Generated premium boss phase 2 texture: {p2_path}")

    # Save Phase 3 Image
    img_p3 = Image.new("RGBA", (1024, 768), (0, 0, 0, 0))
    draw_boss_base(ImageDraw.Draw(img_p3), img_p3, damage_level=2)
    p3_path = os.path.join(data_dir, "dreadnought_phase_3.png")
    _save_png(img_p3, p3_path)
    print(f"[GUI Asset] Generated premium boss phase 3 texture: {p3_path}")

    # Save Destroyed Image
    img_destroyed = Image.new("RGBA", (1024, 768), (0, 0, 0, 0))
    draw_boss_base(ImageDraw.Draw(img_destroyed), img_destroyed, damage_level=3)
    destroyed_path = os.path.join(data_dir, "dreadnought_destroyed.png")
    _save_png(img_destroyed, destroyed_path)
    print(f"[GUI Asset] Generated premium boss destroyed texture: {destroyed_path}")

    # Procedural Player Damage Textures based on static player_skin.png
    player_base_path = os.path.join(data_dir, "player_skin.png")
    if os.path.exists(player_base_path):
        try:
            player_base_img = Image.open(player_base_path)
            # Ensure it is in RGBA mode
            if player_base_img.mode != "RGBA":
                player_base_img = player_base_img.convert("RGBA")
        except Exception as e:
            print(f"[Warning] Failed to load static player_skin.png: {e}. Generating procedural fallback.")
            player_base_img = None
    else:
        player_base_img = None

    if player_base_img is None:
        # Fallback procedural generation of a player ship chevron card (512x512)
        player_base_img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        draw_p = ImageDraw.Draw(player_base_img)
        # Draw a beautiful cyber cyan ship
        draw_p.polygon([(256, 64), (448, 448), (256, 352), (64, 448)], fill=(0, 180, 255, 255), outline=(200, 255, 255, 255), width=8)

    w, h = player_base_img.size

    def draw_player_damage(base_img, damage_level=0):
        # Create a copy so we do not mutate the base image
        img = base_img.copy()
        draw = ImageDraw.Draw(img)
        
        if damage_level >= 1:
            # 75% HP: Light transparent dark-grey/black scorch marks
            draw.ellipse([(int(w * 0.2), int(h * 0.5)), (int(w * 0.35), int(h * 0.65))], fill=(10, 10, 10, 120))
            draw.ellipse([(int(w * 0.45), int(h * 0.2)), (int(w * 0.55), int(h * 0.3))], fill=(20, 20, 20, 140))
            
        if damage_level >= 2:
            # 50% HP: Darker/wider scorch marks and cracked wing plating lines
            draw.ellipse([(int(w * 0.65), int(h * 0.55)), (int(w * 0.8), int(h * 0.7))], fill=(10, 10, 10, 180))
            draw.line([(int(w * 0.25), int(h * 0.5)), (int(w * 0.15), int(h * 0.6))], fill=(50, 50, 50, 255), width=4)
            draw.line([(int(w * 0.75), int(h * 0.5)), (int(w * 0.85), int(h * 0.6))], fill=(50, 50, 50, 255), width=4)
            
        if damage_level >= 3:
            # 25% HP: Extensive scorch marks, heavy cracks, and a small glowing amber/orange warning breach
            draw.ellipse([(int(w * 0.15), int(h * 0.45)), (int(w * 0.35), int(h * 0.65))], fill=(5, 5, 5, 210))
            draw.ellipse([(int(w * 0.65), int(h * 0.45)), (int(w * 0.85), int(h * 0.65))], fill=(5, 5, 5, 210))
            draw.line([(int(w * 0.3), int(h * 0.4)), (int(w * 0.2), int(h * 0.6))], fill=(0, 0, 0, 255), width=6)
            draw.ellipse([(int(w * 0.38), int(h * 0.5)), (int(w * 0.46), int(h * 0.58))], fill=(255, 120, 0, 220), outline=(255, 200, 50, 255), width=4)
            
        if damage_level >= 4:
            # Critical HP: Severe charred/blackened texture, heavy wing breaches, glowing red warning breaches
            black_overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            bo_draw = ImageDraw.Draw(black_overlay)
            bo_draw.rectangle([(int(w * 0.1), int(h * 0.3)), (int(w * 0.9), int(h * 0.85))], fill=(0, 0, 0, 160))
            img = Image.alpha_composite(img, black_overlay)
            draw = ImageDraw.Draw(img)
            draw.ellipse([(int(w * 0.18), int(h * 0.5)), (int(w * 0.28), int(h * 0.6))], fill=(0, 0, 0, 0))
            draw.ellipse([(int(w * 0.38), int(h * 0.5)), (int(w * 0.46), int(h * 0.58))], fill=(255, 0, 0, 255), outline=(255, 100, 100, 255), width=4)
            draw.ellipse([(int(w * 0.54), int(h * 0.54)), (int(w * 0.62), int(h * 0.62))], fill=(255, 0, 0, 255), outline=(255, 100, 100, 255), width=4)

        return img

    # Save player damage states
    for dl, lvl in [(0, "100"), (1, "75"), (2, "50"), (3, "25"), (4, "critical")]:
        dmg_img = draw_player_damage(player_base_img, dl)
        out_name = f"player_hull_{lvl}.png"
        out_path = os.path.join(data_dir, out_name)
        _save_png(dmg_img, out_path)
        print(f"[GUI Asset] Generated premium player hull damage state texture ({lvl}%): {out_path}")



if __name__ == "__main__":
    generate_gui_assets()
