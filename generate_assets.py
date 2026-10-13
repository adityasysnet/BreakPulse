"""
Brand new icon generator for BreakPulse.
Concept: A modern squircle badge with an emerald-to-cyan focus ring,
featuring a stylized 'Pause & Leaf' symbol representing Rest, Mindful Pauses, and Vitality.
"""

import math
from PIL import Image, ImageDraw

def create_breakpulse_icon():
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Base Squircle / Rounded Container
    margin = 12
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=56,
        fill=(15, 23, 42, 255),       # Dark Slate 900
        outline=(51, 65, 85, 255),   # Slate 700
        width=4
    )

    # 2. Glowing Progress / Zen Ring Arc
    center = size // 2
    r = 82
    # Background ring track
    draw.arc(
        [center - r, center - r, center + r, center + r],
        start=0,
        end=360,
        fill=(30, 41, 59, 255),
        width=12
    )
    # Active Emerald to Cyan Arc
    draw.arc(
        [center - r, center - r, center + r, center + r],
        start=-90,
        end=170,
        fill=(16, 185, 129, 255),  # Emerald 500
        width=12
    )

    # 3. Center Icon: "Pause & Sprout/Leaf" (Rest + Vitality)
    # Left Pause Bar
    bar_w = 16
    bar_h = 64
    x_left = center - 28
    y_top = center - (bar_h // 2) + 2
    draw.rounded_rectangle(
        [x_left, y_top, x_left + bar_w, y_top + bar_h],
        radius=8,
        fill=(52, 211, 153, 255)  # Light Emerald
    )

    # Right Pause Bar with a soothing Zen curve / Leaf crest
    x_right = center + 12
    draw.rounded_rectangle(
        [x_right, y_top + 12, x_right + bar_w, y_top + bar_h],
        radius=8,
        fill=(56, 189, 248, 255)  # Sky Blue 400
    )

    # Leaf Sprout crowning the right bar
    # Leaf path curving up and right
    leaf_tip = (x_right + bar_w + 12, y_top - 12)
    leaf_base = (x_right + 4, y_top + 12)
    leaf_ctrl1 = (x_right + bar_w + 20, y_top)
    leaf_ctrl2 = (x_right - 6, y_top - 6)

    # Draw small elegant leaf polygon
    leaf_poly = [
        leaf_base,
        (x_right + 18, y_top - 2),
        leaf_tip,
        (x_right + 6, y_top - 8),
        leaf_base
    ]
    draw.polygon(leaf_poly, fill=(52, 211, 153, 255))

    # Dot accent above right leaf tip (droplet of rest / tea / rejuvenation)
    draw.ellipse(
        [leaf_tip[0] + 4, leaf_tip[1] - 4, leaf_tip[0] + 12, leaf_tip[1] + 4],
        fill=(56, 189, 248, 255)
    )

    # Save 256x256 PNG
    img.save("icon.png", format="PNG")

    # Also save small logo for header (32x32 and 48x48)
    logo_small = img.resize((32, 32), Image.Resampling.LANCZOS)
    logo_small.save("logo_32.png", format="PNG")

    # Save multi-size ICO
    icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save("icon.ico", format="ICO", sizes=icon_sizes)
    print("New BreakPulse icons generated: icon.png, icon.ico, logo_32.png")

if __name__ == "__main__":
    create_breakpulse_icon()
