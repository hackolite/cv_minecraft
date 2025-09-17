#!/usr/bin/env python3
"""
Show username input functionality in action.
This simulates what happens when a user starts the client.
"""

import os
import platform

def simulate_client_startup():
    """Simulate what happens when the client starts up."""
    print("🎮 MINECRAFT CLIENT STARTUP SIMULATION")
    print("=" * 40)
    print("This shows what happens when a user starts the client:")
    print()
    
    # Simulate the startup sequence
    print("=== Minecraft Client ===")
    
    # Show platform detection
    current_platform = platform.system() 
    print(f"Detected platform: {current_platform}")
    
    # Show environment detection
    if current_platform == "Windows":
        username_env = os.environ.get("USERNAME", "TestUser")
        print(f"Windows USERNAME: {username_env}")
        prompt_text = f"Enter your username (default: {username_env}): "
    else:
        username_env = os.environ.get("USER", "testuser")
        print(f"Unix USER: {username_env}")
        prompt_text = f"Enter your username (default: {username_env}): "
    
    print()
    print("User would see this prompt:")
    print(f">>> {prompt_text}")
    print()
    print("Examples of what users can do:")
    print("1. Press Enter → uses system username:", username_env)
    print("2. Type 'MyName' → uses custom username: MyName")
    print("3. Type 'John Doe' → cleaned to: John_Doe")
    print("4. Press Ctrl+C → uses system username:", username_env)
    print()
    
    # Show validation examples
    print("Username validation examples:")
    test_names = [
        username_env,
        "MinecraftPlayer",
        "John Doe",
        "VeryLongUsernameThatExceedsThirtyTwoCharacterLimit",
        "",
        "Player123"
    ]
    
    for name in test_names:
        cleaned = name.replace(" ", "_")[:32] if name else "Player"
        if not cleaned:
            cleaned = "Player"
        print(f"  '{name}' → '{cleaned}'")
    
    print()
    print("✅ After username input, client would:")
    print("   1. Create Window with username")
    print("   2. Connect to server")
    print("   3. Send player_join with username")
    print("   4. Start rendering with username labels")

if __name__ == "__main__":
    simulate_client_startup()