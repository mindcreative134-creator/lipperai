import os
from PIL import Image, ImageDraw, ImageFont

def create_app_logo(output_path: str = "mobile_app/assets/logo.png"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    size = (512, 512)
    img = Image.new("RGBA", size, (11, 15, 25, 255))
    draw = ImageDraw.Draw(img)

    # 1. Outer Neon Glow Shield
    margin = 40
    rounded_rect = [margin, margin, size[0] - margin, size[1] - margin]
    
    # Gradient background simulated with concentric rounded rects
    for i in range(120):
        alpha = int(255 * (1 - i / 180))
        r = int(99 + (236 - 99) * (i / 120))
        g = int(102 - 30 * (i / 120))
        b = int(241 - 88 * (i / 120))
        curr_rect = [margin + i, margin + i, size[0] - margin - i, size[1] - margin - i]
        draw.rounded_rectangle(curr_rect, radius=90 - int(i * 0.4), fill=(r, g, b, 255))

    # Inner Dark Card
    inner_margin = 85
    inner_rect = [inner_margin, inner_margin, size[0] - inner_margin, size[1] - inner_margin]
    draw.rounded_rectangle(inner_rect, radius=60, fill=(17, 24, 39, 240))

    # 2. Draw Vector Scissors Symbol
    # Left ring
    draw.ellipse([145, 300, 215, 370], outline=(236, 72, 153, 255), width=16)
    # Right ring
    draw.ellipse([297, 300, 367, 370], outline=(99, 102, 241, 255), width=16)
    
    # Crossed blades
    draw.line([(190, 320), (330, 160)], fill=(255, 255, 255, 255), width=16)
    draw.line([(322, 320), (182, 160)], fill=(255, 255, 255, 255), width=16)
    
    # Pivot screw
    draw.ellipse([244, 230, 268, 254], fill=(255, 255, 255, 255))

    # 3. AI Magic Sparkles
    # Star 1 (Top Right)
    cx, cy = 360, 140
    draw.polygon([(cx, cy-22), (cx+7, cy-7), (cx+22, cy), (cx+7, cy+7), (cx, cy+22), (cx-7, cy+7), (cx-22, cy), (cx-7, cy-7)], fill=(250, 204, 21, 255))

    # Star 2 (Bottom Left)
    cx2, cy2 = 140, 240
    draw.polygon([(cx2, cy2-14), (cx2+5, cy2-5), (cx2+14, cy2), (cx2+5, cy2+5), (cx2, cy2+14), (cx2-5, cy2+5), (cx2-14, cy2), (cx2-5, cy2-5)], fill=(129, 140, 248, 255))

    # 4. Save 512x512 logo
    img.save(output_path, "PNG")
    print(f"Generated App Logo: {output_path}")

if __name__ == "__main__":
    create_app_logo()

