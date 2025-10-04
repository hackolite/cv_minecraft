#!/usr/bin/env python3
"""
Camera Screenshot Generator
============================

Complete workflow script that queries camera view and generates screenshot.

This script combines camera_view_query.py and camera_view_reconstruction.py
into a single convenient command.

Usage:
    # Generate screenshot from first available camera
    python3 generate_camera_screenshot.py
    
    # Generate screenshot from specific camera
    python3 generate_camera_screenshot.py --camera-id camera_0
    
    # Custom rotation and view distance
    python3 generate_camera_screenshot.py --rotation 45 -10 --view-distance 30
"""

import asyncio
import argparse
import sys
import os

# Import the query and reconstruction modules
from camera_view_query import query_camera_view, save_view_data
from camera_view_reconstruction import load_view_data, render_camera_view, save_screenshot


async def generate_screenshot(
    server_uri: str = "ws://localhost:8765",
    camera_id: str = None,
    rotation: tuple = (0, 0),
    view_distance: float = 50.0,
    output_image: str = "screenshot.png",
    temp_data_file: str = "camera_view_data.json",
    width: int = 800,
    height: int = 600,
    fov: float = 70.0,
    keep_json: bool = False
) -> int:
    """Complete workflow to generate camera screenshot.
    
    Args:
        server_uri: WebSocket server URI
        camera_id: Specific camera block_id (None = first available)
        rotation: Camera rotation (horizontal, vertical)
        view_distance: View distance
        output_image: Output screenshot filename
        temp_data_file: Temporary JSON data file
        width: Image width
        height: Image height
        fov: Field of view in degrees
        keep_json: Keep the intermediate JSON file
        
    Returns:
        Exit code (0 = success, 1 = error)
    """
    print("=" * 70)
    print("Camera Screenshot Generator")
    print("=" * 70)
    
    try:
        # Step 1: Query camera view data
        print("\n📡 Step 1: Querying camera view data...")
        print("-" * 70)
        
        view_data = await query_camera_view(
            server_uri=server_uri,
            camera_id=camera_id,
            rotation=rotation,
            view_distance=view_distance
        )
        
        # Check for errors
        if "error" in view_data:
            print(f"\n❌ Query failed: {view_data['error']}")
            return 1
        
        # Extract the actual camera_id used (might be different if none was specified)
        actual_camera_id = view_data["camera"]["block_id"]
        print(f"📷 Using camera: {actual_camera_id}")
        
        # Determine output path - save in recordings/{camera_id}/ directory
        if output_image == "screenshot.png":
            # Default name - use camera-specific directory
            camera_dir = f"recordings/{actual_camera_id}"
            os.makedirs(camera_dir, exist_ok=True)
            
            # Generate timestamp-based filename
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_image = os.path.join(camera_dir, f"screenshot_{timestamp}.png")
            print(f"💾 Output will be saved to camera directory: {output_image}")
        else:
            # Custom output path specified - still ensure parent directory exists
            output_dir = os.path.dirname(output_image)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            print(f"💾 Output will be saved to: {output_image}")
        
        # Save intermediate data
        save_view_data(view_data, temp_data_file)
        
        # Step 2: Reconstruct and render
        print("\n🎨 Step 2: Reconstructing camera view...")
        print("-" * 70)
        
        img = render_camera_view(
            view_data,
            width=width,
            height=height,
            fov=fov
        )
        
        # Save screenshot
        save_screenshot(img, output_image)
        print(f"📁 Screenshot saved in camera directory: {output_image}")
        
        # Clean up temporary file unless requested to keep
        if not keep_json and os.path.exists(temp_data_file):
            os.remove(temp_data_file)
            print(f"🗑️  Removed temporary file: {temp_data_file}")
        elif keep_json:
            print(f"💾 Kept view data file: {temp_data_file}")
        
        print("\n" + "=" * 70)
        print(f"✅ Screenshot generated successfully: {output_image}")
        print("=" * 70)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate camera screenshot from Minecraft server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --camera-id camera_0
  %(prog)s --rotation 45 -10 --view-distance 30
  %(prog)s --output my_screenshot.png --width 1920 --height 1080
        """
    )
    
    # Connection options
    conn_group = parser.add_argument_group('Connection')
    conn_group.add_argument(
        "--server",
        default="ws://localhost:8765",
        help="WebSocket server URI (default: ws://localhost:8765)"
    )
    
    # Camera options
    cam_group = parser.add_argument_group('Camera')
    cam_group.add_argument(
        "--camera-id",
        help="Specific camera block_id to use (default: first available)"
    )
    cam_group.add_argument(
        "--rotation",
        nargs=2,
        type=float,
        default=[0, 0],
        metavar=("H", "V"),
        help="Camera rotation in degrees (horizontal vertical, default: 0 0)"
    )
    cam_group.add_argument(
        "--view-distance",
        type=float,
        default=50.0,
        help="View distance (default: 50.0)"
    )
    
    # Output options
    out_group = parser.add_argument_group('Output')
    out_group.add_argument(
        "--output",
        default="screenshot.png",
        help="Output screenshot file (default: screenshot.png)"
    )
    out_group.add_argument(
        "--width",
        type=int,
        default=800,
        help="Image width in pixels (default: 800)"
    )
    out_group.add_argument(
        "--height",
        type=int,
        default=600,
        help="Image height in pixels (default: 600)"
    )
    out_group.add_argument(
        "--fov",
        type=float,
        default=70.0,
        help="Field of view in degrees (default: 70.0)"
    )
    out_group.add_argument(
        "--keep-json",
        action="store_true",
        help="Keep intermediate JSON data file"
    )
    
    args = parser.parse_args()
    
    # Generate screenshot
    exit_code = await generate_screenshot(
        server_uri=args.server,
        camera_id=args.camera_id,
        rotation=tuple(args.rotation),
        view_distance=args.view_distance,
        output_image=args.output,
        width=args.width,
        height=args.height,
        fov=args.fov,
        keep_json=args.keep_json
    )
    
    return exit_code


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
