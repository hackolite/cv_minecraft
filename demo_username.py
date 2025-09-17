#!/usr/bin/env python3
"""
Demo script to show username input functionality.
This demonstrates the client's username input without starting the full GUI.
"""

import os
import platform
import sys

# Add the current directory to path to import client functions
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def demo_username_input():
    """Demonstrate the username input functionality."""
    print("=== Minecraft Client - Username Demo ===\n")
    
    # Show platform detection
    current_platform = platform.system()
    print(f"Platform detected: {current_platform}")
    
    # Show environment variable detection
    if current_platform == "Windows":
        current_user = os.environ.get("USERNAME")
        print(f"Windows username from environment: {current_user}")
    else:
        current_user = os.environ.get("USER") or os.environ.get("LOGNAME")
        print(f"Unix username from environment: {current_user}")
    
    print(f"Detected system username: {current_user or 'None'}\n")
    
    # Simulate the get_username function logic
    if current_user:
        print(f"The client would prompt: 'Enter your username (default: {current_user}): '")
        print("This allows users to:")
        print("- Press Enter to use their system username")
        print("- Type a custom username")
        print("- Use Ctrl+C to use the default")
    else:
        print("The client would prompt: 'Enter your username: '")
        print("This prompts for a custom username with 'Player' as fallback")
    
    print(f"\nExample usernames that would be accepted:")
    print("- System username: ", (current_user or "Player").replace(" ", "_")[:32])
    print("- Custom: MyMinecraftName")
    print("- With spaces: 'John Doe' -> 'John_Doe'")
    print("- Long name: 'VeryLongUsernameThatExceedsLimit' -> 'VeryLongUsernameThatExceedsLimi'")
    
    print(f"\n✅ Username functionality ready for Windows and Unix systems!")
    
if __name__ == "__main__":
    demo_username_input()