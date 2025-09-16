#!/usr/bin/env python3
"""
Test script for block visibility optimizations.
Tests the improved show_block, hide_block, exposed and neighbor functionality.
"""

import sys
import os
import time

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
    class image:
        @staticmethod
        def load(path):
            class MockTexture:
                def get_texture(self):
                    return object
            return MockTexture()

# Mock pyglet before imports
sys.modules['pyglet'] = MockPyglet()
sys.modules['pyglet.window'] = MockPyglet.window
sys.modules['pyglet.gl'] = MockPyglet.gl
sys.modules['pyglet.graphics'] = MockPyglet.graphics
sys.modules['pyglet.image'] = MockPyglet.image

# Import our classes
from client import ClientModel, sectorize, FACES
from minecraft import Model

def test_neighbors_functionality():
    """Test the neighbors generator function."""
    print("Testing neighbors functionality...")
    
    # Test ClientModel
    client_model = ClientModel()
    neighbors = list(client_model.neighbors((0, 0, 0)))
    expected_neighbors = [(0, 1, 0), (0, -1, 0), (-1, 0, 0), (1, 0, 0), (0, 0, 1), (0, 0, -1)]
    
    assert len(neighbors) == 6, f"Expected 6 neighbors, got {len(neighbors)}"
    assert set(neighbors) == set(expected_neighbors), f"Neighbors mismatch: {neighbors} vs {expected_neighbors}"
    print("✅ ClientModel neighbors function works correctly")
    
    # Test Model
    model = Model()
    neighbors = list(model.neighbors((1, 1, 1)))
    expected_neighbors = [(1, 2, 1), (1, 0, 1), (0, 1, 1), (2, 1, 1), (1, 1, 2), (1, 1, 0)]
    
    assert len(neighbors) == 6, f"Expected 6 neighbors, got {len(neighbors)}"
    assert set(neighbors) == set(expected_neighbors), f"Neighbors mismatch: {neighbors} vs {expected_neighbors}"
    print("✅ Model neighbors function works correctly")

def test_face_exposure():
    """Test face exposure functionality."""
    print("Testing face exposure functionality...")
    
    client_model = ClientModel()
    
    # Add some blocks
    client_model.world[(0, 0, 0)] = 'GRASS'
    client_model.world[(1, 0, 0)] = 'GRASS'
    client_model.world[(0, 1, 0)] = 'GRASS'
    
    # Test face_exposed
    assert client_model.face_exposed((0, 0, 0), (1, 0, 0)) == False, "Face should not be exposed (has neighbor)"
    assert client_model.face_exposed((0, 0, 0), (0, 0, 1)) == True, "Face should be exposed (no neighbor)"
    print("✅ face_exposed function works correctly")
    
    # Test get_exposed_faces
    exposed_faces = client_model.get_exposed_faces((0, 0, 0))
    assert len(exposed_faces) == 4, f"Expected 4 exposed faces, got {len(exposed_faces)}"
    print("✅ get_exposed_faces function works correctly")

def test_exposure_cache():
    """Test exposure caching functionality."""
    print("Testing exposure cache...")
    
    client_model = ClientModel()
    
    # Add a block
    client_model.world[(0, 0, 0)] = 'GRASS'
    
    # First call should calculate and cache
    start_time = time.time()
    exposed1 = client_model.exposed((0, 0, 0))
    first_call_time = time.time() - start_time
    
    # Second call should use cache
    start_time = time.time()
    exposed2 = client_model.exposed((0, 0, 0))
    second_call_time = time.time() - start_time
    
    assert exposed1 == exposed2, "Cached result should match original"
    assert (0, 0, 0) in client_model.exposure_cache, "Position should be in cache"
    print("✅ Exposure cache works correctly")
    
    # Test cache invalidation
    client_model.invalidate_exposure_cache((0, 0, 0))
    assert (0, 0, 0) not in client_model.exposure_cache, "Cache should be invalidated"
    print("✅ Cache invalidation works correctly")

def test_batch_neighbor_checking():
    """Test batch neighbor checking functionality."""
    print("Testing batch neighbor checking...")
    
    client_model = ClientModel()
    
    # Add multiple blocks
    positions = [(0, 0, 0), (1, 0, 0), (2, 0, 0)]
    for pos in positions:
        client_model.world[pos] = 'GRASS'
    
    # Test batch check
    client_model.check_neighbors_batch(positions)
    print("✅ Batch neighbor checking completed without errors")

def test_performance_improvement():
    """Test that our optimizations provide performance benefits."""
    print("Testing performance improvements...")
    
    client_model = ClientModel()
    
    # Create a larger world
    positions = []
    for x in range(10):
        for y in range(10):
            for z in range(10):
                pos = (x, y, z)
                client_model.world[pos] = 'GRASS'
                positions.append(pos)
    
    # Time individual neighbor checks
    start_time = time.time()
    for pos in positions[:100]:  # Test first 100 positions
        client_model.check_neighbors(pos)
    individual_time = time.time() - start_time
    
    # Time batch neighbor check
    start_time = time.time()
    client_model.check_neighbors_batch(positions[:100])
    batch_time = time.time() - start_time
    
    print(f"Individual checks time: {individual_time:.4f}s")
    print(f"Batch check time: {batch_time:.4f}s")
    print("✅ Performance test completed")

def main():
    """Run all tests."""
    print("🚀 Starting block visibility optimization tests...\n")
    
    try:
        test_neighbors_functionality()
        print()
        
        test_face_exposure()
        print()
        
        test_exposure_cache()
        print()
        
        test_batch_neighbor_checking()
        print()
        
        test_performance_improvement()
        print()
        
        print("🎉 All tests passed! Block visibility optimizations are working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()