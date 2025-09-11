#!/usr/bin/env python3
"""
Quick validation script to confirm the block visibility fix is working.
Run this to verify that blocks should now be visible in the game.
"""

import sys
import os

def validate_fix():
    """Validate that the block visibility fix is properly applied."""
    print("🔧 Validating Block Visibility Fix")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists('pyglet_client.py'):
        print("❌ Please run this script from the cv_minecraft directory")
        return False
    
    success = True
    
    # 1. Check pyglet_client.py
    print("1. Checking pyglet_client.py...")
    try:
        with open('pyglet_client.py', 'r') as f:
            content = f.read()
        
        if 'self.position = (12, 20, 12)' in content:
            print("   ✅ Position fixed to (12, 20, 12)")
        elif 'self.position = (30, 50, 80)' in content:
            print("   ❌ Still using old position (30, 50, 80)")
            success = False
        else:
            print("   ⚠️  Position line not found or modified")
    except Exception as e:
        print(f"   ❌ Error reading file: {e}")
        success = False
    
    # 2. Check minecraft.py
    print("2. Checking minecraft.py...")
    try:
        with open('minecraft.py', 'r') as f:
            content = f.read()
        
        if 'self.position = (12, 20, 12)' in content:
            print("   ✅ Position fixed to (12, 20, 12)")
        elif 'self.position = (30, 50, 80)' in content:
            print("   ❌ Still using old position (30, 50, 80)")
            success = False
        else:
            print("   ⚠️  Position line not found or modified")
    except Exception as e:
        print(f"   ❌ Error reading file: {e}")
        success = False
    
    # 3. Check client.py
    print("3. Checking client.py...")
    try:
        with open('client.py', 'r') as f:
            content = f.read()
        
        if 'self.position = Vec3(12, 20, 12)' in content:
            print("   ✅ Position fixed to Vec3(12, 20, 12)")
        elif 'self.position = Vec3(32, 32, 25)' in content:
            print("   ❌ Still using old position Vec3(32, 32, 25)")
            success = False
        else:
            print("   ⚠️  Position line not found or modified")
    except Exception as e:
        print(f"   ❌ Error reading file: {e}")
        success = False
    
    # 4. Verify dependencies
    print("4. Checking dependencies...")
    try:
        import pyglet
        print("   ✅ Pyglet installed")
    except ImportError:
        print("   ❌ Pyglet not installed (run: pip install -r requirements.txt)")
        success = False
    
    try:
        import websockets
        print("   ✅ WebSockets installed")
    except ImportError:
        print("   ❌ WebSockets not installed (run: pip install -r requirements.txt)")
        success = False
    
    # 5. Check texture file
    print("5. Checking texture file...")
    if os.path.exists('texture.png'):
        print("   ✅ Texture file exists")
    else:
        print("   ❌ Texture file missing")
        success = False
    
    print("\n📊 Validation Results:")
    print("=" * 25)
    
    if success:
        print("✅ ALL CHECKS PASSED!")
        print("\n🎉 Block Visibility Fix Applied Successfully!")
        print("\n📋 What was fixed:")
        print("   • Player spawn position moved from outside world to center")
        print("   • OLD: (30, 50, 80) - completely outside generated world")
        print("   • NEW: (12, 20, 12) - center of world at good viewing height")
        print("   • World bounds: X(0-23), Y(-15 to 16), Z(0-23)")
        print("\n🎮 To test the fix:")
        print("   1. Start server: python3 server.py")
        print("   2. Start client: python3 pyglet_client.py")
        print("   3. You should now see blocks in the world!")
        print("   4. Use WASD/ZQSD keys to move around")
        print("   5. Use mouse to look around")
        print("   6. Left click to remove blocks, right click to place blocks")
        
        return True
    else:
        print("❌ SOME CHECKS FAILED!")
        print("\n🔧 The fix may not be properly applied.")
        print("Please check the error messages above and fix any issues.")
        return False

def main():
    """Main function."""
    result = validate_fix()
    
    if not result:
        print("\n💡 If you're still having issues:")
        print("   • Make sure you're in the cv_minecraft directory")
        print("   • Run: pip install -r requirements.txt")
        print("   • Check that all files were properly updated")
    
    return result

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)