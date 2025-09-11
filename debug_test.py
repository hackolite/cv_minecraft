#!/usr/bin/env python3
"""
Debug test for the new protocol
"""

import asyncio
import logging
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client_new.network_client import NetworkClient


async def debug_test():
    """Debug test with detailed logging"""
    # Setup debug logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    client = NetworkClient("DebugPlayer")
    
    try:
        print("Attempting to connect...")
        success = await client.connect("localhost", 8766)
        print(f"Connection result: {success}")
        
        if success:
            print("Waiting for login...")
            await asyncio.sleep(5)
            
            if client.is_connected():
                print("✅ Connection successful!")
            else:
                print("❌ Login failed")
        else:
            print("❌ Connection failed")
            
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client.is_connected():
            await client.disconnect()


if __name__ == "__main__":
    asyncio.run(debug_test())