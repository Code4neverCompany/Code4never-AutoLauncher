"""
Round Corners Utility for Autolauncher Icons and Logos
Applies modern rounded corners to all icon and logo assets.

© 2025 4never Company. All rights reserved.
"""

from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path
import os

def add_rounded_corners(image, radius):
    """
    Add rounded corners to an image with transparency.
    
    Args:
        image: PIL Image object
        radius: Corner radius in pixels
        
    Returns:
        PIL Image with rounded corners and alpha channel
    """
    # Convert to RGBA if not already
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Create a mask for rounded corners
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)
    
    # Draw rounded rectangle on mask
    draw.rounded_rectangle(
        [(0, 0), image.size],
        radius=radius,
        fill=255
    )
    
    # Apply the mask to create rounded corners
    output = Image.new('RGBA', image.size, (0, 0, 0, 0))
    output.paste(image, (0, 0))
    output.putalpha(mask)
    
    return output

def process_icon(input_path, output_path, radius_percent=15):
    """
    Process an icon file to add rounded corners.
    
    Args:
        input_path: Path to input image
        output_path: Path to save output image
        radius_percent: Corner radius as percentage of image size (default 15%)
    """
    print(f"Processing: {input_path}")
    
    # Load image
    img = Image.open(input_path)
    
    # Calculate radius based on image size
    size = min(img.size)
    radius = int(size * radius_percent / 100)
    
    print(f"  Image size: {img.size[0]}x{img.size[1]}")
    print(f"  Corner radius: {radius}px ({radius_percent}%)")
    
    # Apply rounded corners
    rounded_img = add_rounded_corners(img, radius)
    
    # Save with transparency
    rounded_img.save(output_path, 'PNG', optimize=True)
    
    print(f"  ✓ Saved to: {output_path}")
    return rounded_img

def process_logo(input_path, output_path, radius_percent=10):
    """
    Process a logo file to add rounded corners.
    Logos use a smaller radius for subtlety.
    
    Args:
        input_path: Path to input image  
        output_path: Path to save output image
        radius_percent: Corner radius as percentage (default 10%)
    """
    print(f"Processing: {input_path}")
    
    # Load image
    img = Image.open(input_path)
    
    # Calculate radius
    size = min(img.size)
    radius = int(size * radius_percent / 100)
    
    print(f"  Image size: {img.size[0]}x{img.size[1]}")
    print(f"  Corner radius: {radius}px ({radius_percent}%)")
    
    # Apply rounded corners
    rounded_img = add_rounded_corners(img, radius)
    
    # Save as PNG with transparency
    rounded_img.save(output_path, 'PNG', optimize=True)
    
    print(f"  ✓ Saved to: {output_path}")
    return rounded_img

def create_rounded_icon_ico(png_path, ico_path):
    """
    Create a Windows .ico file from rounded PNG.
    
    Args:
        png_path: Path to source PNG file
        ico_path: Path to output ICO file
    """
    print(f"\nCreating Windows icon: {ico_path}")
    
    img = Image.open(png_path)
    
    # Icon sizes for Windows
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    
    # Save as ICO with multiple resolutions
    img.save(ico_path, format='ICO', sizes=icon_sizes)
    
    print(f"  ✓ Created with resolutions: {', '.join([f'{s[0]}x{s[1]}' for s in icon_sizes])}")

def main():
    """Main processing function."""
    print("=" * 60)
    print("  Autolauncher Icon & Logo Rounded Corner Processor")
    print("  © 2025 4never Company. All rights reserved.")
    print("=" * 60)
    print()
    
    # Define paths
    assets_dir = Path("assets")
    backup_dir = assets_dir / "originals"
    
    # Create backup directory
    backup_dir.mkdir(exist_ok=True)
    print(f"Backup directory: {backup_dir}\n")
    
    # Files to process
    files_to_process = [
        {
            'name': 'icon.png',
            'type': 'icon',
            'radius': 15,  # 15% rounded corners for icons
        },
        {
            'name': 'logo_dark.jpg',
            'type': 'logo',
            'radius': 10,  # 10% for logos (more subtle)
        },
        {
            'name': 'logo_light.jpg',
            'type': 'logo',
            'radius': 10,
        }
    ]
    
    # Process each file
    for file_info in files_to_process:
        filename = file_info['name']
        input_path = assets_dir / filename
        
        if not input_path.exists():
            print(f"⚠ Warning: {input_path} not found, skipping")
            continue
        
        # Backup original (only if backup doesn't exist)
        backup_path = backup_dir / filename
        if not backup_path.exists():
            import shutil
            shutil.copy2(input_path, backup_path)
            print(f"✓ Backed up original to: {backup_path}")
        
        # Generate output filename (PNG format for transparency)
        name_without_ext = input_path.stem
        output_filename = f"{name_without_ext}_rounded.png"
        output_path = assets_dir / output_filename
        
        # Process based on type
        if file_info['type'] == 'icon':
            rounded_img = process_icon(input_path, output_path, file_info['radius'])
        else:
            rounded_img = process_logo(input_path, output_path, file_info['radius'])
        
        print()
    
    # Create rounded .ico file from rounded icon
    rounded_icon_png = assets_dir / "icon_rounded.png"
    if rounded_icon_png.exists():
        rounded_ico_path = assets_dir / "icon_rounded.ico"
        create_rounded_icon_ico(rounded_icon_png, rounded_ico_path)
        print()
    
    # Summary
    print("=" * 60)
    print("  Processing Complete!")
    print("=" * 60)
    print()
    print("Rounded files created:")
    print(f"  • {assets_dir / 'icon_rounded.png'}")
    print(f"  • {assets_dir / 'icon_rounded.ico'}")
    print(f"  • {assets_dir / 'logo_dark_rounded.png'}")
    print(f"  • {assets_dir / 'logo_light_rounded.png'}")
    print()
    print("Originals backed up to: assets/originals/")
    print()
    print("Next steps:")
    print("  1. Review the rounded versions")
    print("  2. If satisfied, run: python apply_rounded_icons.py")
    print("     (This will replace the current icons with rounded versions)")
    print()

if __name__ == "__main__":
    main()
