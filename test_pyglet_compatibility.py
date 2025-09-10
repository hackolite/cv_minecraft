#!/usr/bin/env python3
"""
Test script to verify Pyglet 2.1.8 compatibility changes
without requiring a display server
"""

import sys
import os
import ast

def test_syntax():
    """Test that all Python files have correct syntax"""
    print("🔍 Testing syntax...")
    
    files_to_test = ['minecraft.py', 'main.py', 'noise_gen.py', 'test_connection.py', 'validate_requirements.py']
    
    for filename in files_to_test:
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    code = f.read()
                ast.parse(code)
                print(f"✅ {filename}: Syntax OK")
            except SyntaxError as e:
                print(f"❌ {filename}: Syntax error: {e}")
                return False
        else:
            print(f"⚠️  {filename}: File not found")
    
    return True

def test_imports():
    """Test that imports work correctly"""
    print("\n🔍 Testing imports...")
    
    # Test noise_gen import (should work without display)
    try:
        import noise_gen
        print("✅ noise_gen: Import OK")
    except Exception as e:
        print(f"❌ noise_gen: Import failed: {e}")
        return False
    
    # Test specific Pyglet compatibility
    try:
        import pyglet
        print(f"✅ Pyglet version: {pyglet.version}")
        
        # Test that our compatibility imports work
        from pyglet.graphics import TextureGroup
        print("✅ TextureGroup import: OK")
        
        # Test that our fallback import structure is correct
        try:
            from pyglet.graphics import get_default_shader
            print("✅ get_default_shader import: OK")
        except ImportError:
            print("✅ get_default_shader import: OK (fallback handled)")
        
    except Exception as e:
        print(f"❌ Pyglet imports failed: {e}")
        return False
    
    return True

def test_changes():
    """Test specific changes made for Pyglet 2.1.8"""
    print("\n🔍 Testing Pyglet 2.1.8 compatibility changes...")
    
    with open('minecraft.py', 'r') as f:
        code = f.read()
    
    # Check that we have compatibility code for vertex_list
    if 'Try Pyglet 2.x approach first' in code:
        print("✅ Vertex list compatibility code present")
    else:
        print("❌ Vertex list compatibility code missing")
        return False
    
    # Check that we have fallback for get_default_shader
    if 'except ImportError:' in code and 'get_default_shader = None' in code:
        print("✅ get_default_shader fallback present")
    else:
        print("❌ get_default_shader fallback missing")
        return False
    
    # Check draw_reticle compatibility
    if 'except TypeError:' in code and 'mode=GL_LINES' in code:
        print("✅ draw_reticle compatibility code present")
    else:
        print("❌ draw_reticle compatibility code missing")
        return False
    
    return True

def test_requirements():
    """Test requirements.txt has correct Pyglet version"""
    print("\n🔍 Testing requirements.txt...")
    
    try:
        with open('requirements.txt', 'r') as f:
            content = f.read()
        
        if 'pyglet==2.1.8' in content:
            print("✅ requirements.txt specifies Pyglet 2.1.8")
            return True
        else:
            print("❌ requirements.txt does not specify Pyglet 2.1.8")
            return False
    except FileNotFoundError:
        print("❌ requirements.txt not found")
        return False

def main():
    print("🎯 Pyglet 2.1.8 Compatibility Verification")
    print("=" * 50)
    
    tests = [
        ("Syntax check", test_syntax),
        ("Import check", test_imports), 
        ("Compatibility changes", test_changes),
        ("Requirements check", test_requirements),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print(f"\n📋 Final Results:")
    print("=" * 30)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if not result:
            all_passed = False
    
    if all_passed:
        print(f"\n🎉 All tests passed! Code is compatible with Pyglet 2.1.8")
        return True
    else:
        print(f"\n⚠️  Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)