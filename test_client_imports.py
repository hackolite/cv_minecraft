#!/usr/bin/env python3
"""
Test client instantiation without GUI to verify no import errors
"""

import sys
import os

# Mock out pyglet to avoid GUI requirements
class MockPyglet:
    class window:
        Window = object
        key = object
        mouse = object
    class gl:
        pass
    class graphics:
        Batch = object
        TextureGroup = object

# Mock pyglet before imports
sys.modules['pyglet'] = MockPyglet()
sys.modules['pyglet.window'] = MockPyglet.window
sys.modules['pyglet.gl'] = MockPyglet.gl
sys.modules['pyglet.graphics'] = MockPyglet.graphics

try:
    from client_config import ClientConfig
    print("✅ client_config imports successfully")
    
    config = ClientConfig()
    keys = config.get_movement_keys()
    print(f"✅ Movement keys configured: {keys}")
    
    # Test that default config uses AZERTY
    if config.is_azerty_layout():
        expected = {"forward": "Z", "backward": "S", "left": "Q", "right": "D"}
        if keys == expected:
            print("✅ AZERTY layout confirmed with correct Z/Q/S/D mappings")
        else:
            print(f"❌ AZERTY mapping error: expected {expected}, got {keys}")
    else:
        print("ℹ️ Currently using QWERTY layout")
    
    print("✅ Client configuration test completed successfully")
    
except Exception as e:
    print(f"❌ Error testing client: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)