#!/usr/bin/env python3
"""
Demo: Generate Multiple Camera Screenshots
===========================================

This demo generates screenshots from different perspectives to showcase
the camera screenshot system.

It creates:
1. Screenshots from each available camera
2. Screenshots with different rotations
3. A comparison showing the data flow
"""

import asyncio
import sys
import subprocess
from pathlib import Path


async def run_command(cmd, description):
    """Run a command and print its output."""
    print(f"\n{'='*70}")
    print(f"{description}")
    print(f"{'='*70}")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )
    
    stdout, _ = await proc.communicate()
    output = stdout.decode()
    print(output)
    
    return proc.returncode == 0


async def main():
    """Main demo function."""
    print("=" * 70)
    print("Camera Screenshot System Demo")
    print("=" * 70)
    print()
    print("This demo will generate multiple screenshots to showcase the system.")
    print()
    
    output_dir = Path("demo_screenshots")
    output_dir.mkdir(exist_ok=True)
    
    # Demo 1: Screenshot from first camera, default view
    await run_command(
        [
            "python3", "generate_camera_screenshot.py",
            "--camera-id", "camera_0",
            "--output", str(output_dir / "camera0_default.png")
        ],
        "Demo 1: Default view from camera_0"
    )
    
    # Demo 2: Camera with rotation
    await run_command(
        [
            "python3", "generate_camera_screenshot.py",
            "--camera-id", "camera_0",
            "--rotation", "90", "0",
            "--output", str(output_dir / "camera0_rotated_90.png")
        ],
        "Demo 2: Camera_0 rotated 90° to the right"
    )
    
    # Demo 3: Camera looking down
    await run_command(
        [
            "python3", "generate_camera_screenshot.py",
            "--camera-id", "camera_4",
            "--rotation", "0", "-45",
            "--view-distance", "25",
            "--output", str(output_dir / "camera4_looking_down.png")
        ],
        "Demo 3: Camera_4 looking downward at 45°"
    )
    
    # Demo 4: High resolution screenshot
    await run_command(
        [
            "python3", "generate_camera_screenshot.py",
            "--camera-id", "camera_0",
            "--rotation", "180", "0",
            "--width", "1920",
            "--height", "1080",
            "--output", str(output_dir / "camera0_hd.png")
        ],
        "Demo 4: High-resolution screenshot (1920x1080)"
    )
    
    # Demo 5: Keep JSON data for inspection
    await run_command(
        [
            "python3", "generate_camera_screenshot.py",
            "--camera-id", "camera_1",
            "--keep-json",
            "--output", str(output_dir / "camera1_with_json.png")
        ],
        "Demo 5: Generate screenshot and keep JSON data"
    )
    
    # Summary
    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print(f"\nGenerated screenshots are in: {output_dir}/")
    print("\nGenerated files:")
    for file in sorted(output_dir.glob("*")):
        size = file.stat().st_size
        print(f"  - {file.name} ({size:,} bytes)")
    
    print("\n" + "=" * 70)
    print("Next Steps:")
    print("=" * 70)
    print("1. View the generated screenshots")
    print("2. Compare the different camera perspectives")
    print("3. Inspect camera_view_data.json to see the raw data")
    print("4. Try generating your own screenshots with different parameters")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
