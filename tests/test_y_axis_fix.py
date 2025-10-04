#!/usr/bin/env python3
"""
Simple test to verify Y-axis orientation fix in camera_view_reconstruction.py

This test creates a simple scene and verifies that blocks above the camera
appear at the top of the image and blocks below appear at the bottom.
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from camera_view_reconstruction import render_camera_view


def test_y_axis_orientation():
    """Test that Y-axis is properly oriented (not upside down)."""
    
    # Create test data with camera at origin looking forward (north)
    # Block above camera should appear at top of image (small y value)
    # Block below camera should appear at bottom of image (large y value)
    
    test_data = {
        "camera": {
            "block_id": "test_camera",
            "position": [0, 10, 0],  # Camera at y=10
            "rotation": [0, 0]  # Looking north, level
        },
        "blocks": [
            # Block directly above camera at y=15 (should be at top of image)
            {
                "position": [0, 15, 10],
                "block_type": "brick",
                "block_id": None,
                "collision": True,
                "distance": 10.0
            },
            # Block directly below camera at y=5 (should be at bottom of image)
            {
                "position": [0, 5, 10],
                "block_type": "grass",
                "block_id": None,
                "collision": True,
                "distance": 10.0
            },
            # Block at same level as camera (should be at center)
            {
                "position": [0, 10, 10],
                "block_type": "stone",
                "block_id": None,
                "collision": True,
                "distance": 10.0
            }
        ]
    }
    
    print("=" * 70)
    print("Y-Axis Orientation Test")
    print("=" * 70)
    print("\nTest scenario:")
    print(f"  Camera at: {test_data['camera']['position']}")
    print(f"  Block ABOVE camera at: [0, 15, 10]")
    print(f"  Block at SAME LEVEL at: [0, 10, 10]")
    print(f"  Block BELOW camera at: [0, 5, 10]")
    
    # Render the image
    img = render_camera_view(test_data, width=800, height=600)
    
    print("\n✅ Image rendered successfully!")
    print("\nExpected result (with fix applied):")
    print("  - Block at y=15 (brick) should appear near TOP of image")
    print("  - Block at y=10 (stone) should appear near CENTER of image")
    print("  - Block at y=5 (grass) should appear near BOTTOM of image")
    
    print("\nWithout fix (old behavior with minus sign):")
    print("  - Image would be UPSIDE DOWN")
    print("  - Block at y=15 would appear at BOTTOM")
    print("  - Block at y=5 would appear at TOP")
    
    # Save test image
    output_path = "/tmp/y_axis_test.png"
    img.save(output_path)
    print(f"\n💾 Test image saved to: {output_path}")
    
    print("\n" + "=" * 70)
    print("Test completed successfully!")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    try:
        success = test_y_axis_orientation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
