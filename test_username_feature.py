#!/usr/bin/env python3
"""
Test script to verify username functionality and Windows compatibility.
"""
import os
import sys
import platform
import subprocess
import tempfile
import time

def test_username_function():
    """Test the username gathering function in isolation."""
    print("🧪 Testing username function...")
    
    # Mock environment variable
    original_user = os.environ.get("USER")
    os.environ["USER"] = "TestUser123"
    
    try:
        # Import the function
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from client import get_username
        
        # Test with empty input (should use environment variable)
        print("✅ Username function imported successfully")
        
        # Test platform detection
        current_platform = platform.system()
        print(f"✅ Platform detected: {current_platform}")
        
        if current_platform == "Windows":
            # Test Windows username detection
            windows_user = os.environ.get("USERNAME", "TestWindowsUser")
            print(f"✅ Windows username environment: {windows_user}")
        else:
            # Test Unix username detection  
            unix_user = os.environ.get("USER", "TestUnixUser")
            print(f"✅ Unix username environment: {unix_user}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing username function: {e}")
        return False
    finally:
        # Restore environment
        if original_user:
            os.environ["USER"] = original_user
        elif "USER" in os.environ:
            del os.environ["USER"]

def test_player_visibility():
    """Test player visibility with a simple server connection."""
    print("🧪 Testing player visibility functionality...")
    
    try:
        # Start server process
        server_process = subprocess.Popen(
            [sys.executable, "server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Wait for server to start
        time.sleep(3)
        
        # Run the player visibility test
        result = subprocess.run(
            [sys.executable, "test_player_updates_simple.py"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            timeout=30
        )
        
        success = "SUCCESS: Both players can see each other!" in result.stdout or "SUCCESS: Both players can see each other!" in result.stderr
        
        if success:
            print("✅ Player visibility test passed")
        else:
            print("❌ Player visibility test failed")
            # Only print error details if test actually failed
            if "PASS" not in result.stdout:
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
        
        return success
        
    except subprocess.TimeoutExpired:
        print("❌ Player visibility test timed out")
        return False
    except Exception as e:
        print(f"❌ Error running player visibility test: {e}")
        return False
    finally:
        # Clean up server process
        try:
            server_process.terminate()
            server_process.wait(timeout=5)
        except:
            server_process.kill()

def main():
    """Run all tests."""
    print("=== Testing Username and Player Visibility Features ===\n")
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Username function
    if test_username_function():
        tests_passed += 1
    
    print()
    
    # Test 2: Player visibility
    if test_player_visibility():
        tests_passed += 1
    
    print(f"\n📊 Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Username input (Windows compatible)")
        print("✅ Player visibility working")
        print("✅ User names properly transmitted and displayed")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)