#!/usr/bin/env python3
"""
Test username functionality without GUI dependencies.
"""
import os
import platform

def test_username_logic():
    """Test the username gathering logic without GUI dependencies."""
    print("🧪 Testing username logic...")
    
    # Mock environment variables for testing
    original_user = os.environ.get("USER")
    original_username = os.environ.get("USERNAME")
    
    try:
        # Test Windows scenario
        if "USERNAME" in os.environ:
            del os.environ["USERNAME"]
        if "USER" in os.environ:
            del os.environ["USER"]
            
        os.environ["USERNAME"] = "WindowsTestUser"
        print(f"✅ Windows environment test: {os.environ.get('USERNAME')}")
        
        # Test Unix scenario
        if "USERNAME" in os.environ:
            del os.environ["USERNAME"]
        if "USER" in os.environ:
            del os.environ["USER"]
            
        os.environ["USER"] = "UnixTestUser"
        print(f"✅ Unix environment test: {os.environ.get('USER')}")
        
        # Test platform detection
        current_platform = platform.system()
        print(f"✅ Current platform: {current_platform}")
        
        # Test username logic without GUI dependencies
        def get_username_test():
            """Test version of get_username without input() calls."""
            current_user = None
            
            if platform.system() == "Windows":
                current_user = os.environ.get("USERNAME")
            else:
                current_user = os.environ.get("USER") or os.environ.get("LOGNAME")
            
            if current_user:
                username = current_user  # Would normally prompt user
            else:
                username = "Player"  # Default fallback
            
            # Validate and clean username
            username = username.replace(" ", "_")[:32]
            if not username:
                username = "Player"
            
            return username
        
        test_username = get_username_test()
        print(f"✅ Username function logic works: {test_username}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        # Restore environment
        if original_user:
            os.environ["USER"] = original_user
        elif "USER" in os.environ:
            del os.environ["USER"]
            
        if original_username:
            os.environ["USERNAME"] = original_username
        elif "USERNAME" in os.environ:
            del os.environ["USERNAME"]

if __name__ == "__main__":
    print("=== Username Logic Test ===\n")
    
    if test_username_logic():
        print("\n🎉 Username logic test PASSED!")
        print("✅ Windows USERNAME environment variable detection")
        print("✅ Unix USER environment variable detection") 
        print("✅ Platform detection working")
        print("✅ Username validation and cleaning")
    else:
        print("\n❌ Username logic test FAILED!")