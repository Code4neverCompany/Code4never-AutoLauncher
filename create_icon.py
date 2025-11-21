"""
Utility script to create Windows .ico file from PNG image.
Creates multi-resolution icons suitable for Windows applications.
"""

from PIL import Image
import os

def create_icon_from_png(png_path, ico_path):
    """
    Convert PNG to ICO with multiple resolutions.
    
    Args:
        png_path: Path to source PNG file
        ico_path: Path to output ICO file
    """
    try:
        # Open the PNG image
        img = Image.open(png_path)
        
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Define icon sizes (Windows standard)
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        
        # Create resized versions
        icon_images = []
        for size in icon_sizes:
            resized = img.resize(size, Image.Resampling.LANCZOS)
            icon_images.append(resized)
        
        # Save as ICO
        img.save(ico_path, format='ICO', sizes=icon_sizes)
        print(f"✓ Successfully created {ico_path}")
        print(f"  Icon resolutions: {', '.join([f'{s[0]}x{s[1]}' for s in icon_sizes])}")
        
    except Exception as e:
        print(f"✗ Error creating icon: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Paths
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    png_path = os.path.join(assets_dir, "icon.png")
    ico_path = os.path.join(assets_dir, "icon.ico")
    
    # Check if PNG exists
    if not os.path.exists(png_path):
        print(f"✗ Error: PNG file not found at {png_path}")
        exit(1)
    
    # Create icon
    print(f"Creating Windows icon from {png_path}...")
    if create_icon_from_png(png_path, ico_path):
        print("\n✓ Icon creation complete!")
    else:
        print("\n✗ Icon creation failed!")
        exit(1)
