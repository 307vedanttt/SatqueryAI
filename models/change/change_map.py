"""
Optional: generate a visual change heatmap as a PNG.
"""
import numpy as np
from PIL import Image

def generate_change_heatmap(img1_path: str, img2_path: str, output_path: str) -> str:
    """Generates a change heatmap between two images and saves it."""
    img1 = Image.open(img1_path).convert("L")
    img2 = Image.open(img2_path).convert("L")
    
    if img1.size != img2.size:
        img2 = img2.resize(img1.size)
        
    arr1 = np.array(img1, dtype=np.float32)
    arr2 = np.array(img2, dtype=np.float32)
    
    diff = np.abs(arr1 - arr2)
    
    if diff.max() > 0:
        diff_norm = diff / diff.max()
    else:
        diff_norm = diff
        
    # colormap: red to blue gradient (0=blue, 255=red)
    # R: 255 * diff_norm, G: 0, B: 255 * (1 - diff_norm)
    r = (255 * diff_norm).astype(np.uint8)
    g = np.zeros_like(r)
    b = (255 * (1 - diff_norm)).astype(np.uint8)
    
    colored_diff_uint8 = np.stack([r, g, b], axis=-1)
    heatmap_img = Image.fromarray(colored_diff_uint8, mode="RGB")
    
    heatmap_img.save(output_path)
    
    return output_path
