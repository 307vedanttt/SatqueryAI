"""
SatQuery AI — Change Map Generator (Person C, Optional)

Computes pixel-level difference heatmap and saves as PNG.
"""

from PIL import Image, ImageChops, ImageOps


def generate_change_heatmap(img1_path: str, img2_path: str, output_path: str) -> str:
    """Generate pixel difference heatmap PNG image."""
    img1 = Image.open(img1_path).convert("RGB")
    img2 = Image.open(img2_path).convert("RGB")

    # Resize img2 to match img1 if needed
    if img1.size != img2.size:
        img2 = img2.resize(img1.size)

    diff = ImageChops.difference(img1, img2)
    gray_diff = diff.convert("L")
    heatmap = ImageOps.colorize(gray_diff, black="black", white="red")

    heatmap.save(output_path)
    return output_path
