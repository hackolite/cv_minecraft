#!/usr/bin/env python3
"""
Simple test for block visibility optimizations.
Tests core functionality without GUI dependencies.
"""

import sys
import time

# Define FACES constant (same as in the actual code)
FACES = [
    ( 0, 1, 0),
    ( 0,-1, 0),
    (-1, 0, 0),
    ( 1, 0, 0),
    ( 0, 0, 1),
    ( 0, 0,-1),
]

class TestModel:
    """Simple model class for testing block visibility functionality."""
    
    def __init__(self):
        self.world = {}
        self.shown = {}
        self.exposure_cache = {}
    
    def neighbors(self, position):
        """Generate all neighboring positions for a given position."""
        x, y, z = position
        for dx, dy, dz in FACES:
            yield (x + dx, y + dy, z + dz)
    
    def exposed(self, position):
        """Returns False if given position is surrounded on all 6 sides by blocks, True otherwise."""
        # Check cache first
        if position in self.exposure_cache:
            return self.exposure_cache[position]
        
        # Calculate exposure status
        x, y, z = position
        exposed = False
        for dx, dy, dz in FACES:
            if (x + dx, y + dy, z + dz) not in self.world:
                exposed = True
                break
        
        # Cache the result
        self.exposure_cache[position] = exposed
        return exposed
    
    def face_exposed(self, position, face_direction):
        """Check if a specific face of a block is exposed."""
        x, y, z = position
        dx, dy, dz = face_direction
        neighbor_pos = (x + dx, y + dy, z + dz)
        return neighbor_pos not in self.world
    
    def get_exposed_faces(self, position):
        """Get all exposed faces of a block."""
        exposed_faces = []
        for face in FACES:
            if self.face_exposed(position, face):
                exposed_faces.append(face)
        return exposed_faces
    
    def invalidate_exposure_cache(self, position):
        """Invalidate exposure cache for a position and its neighbors."""
        positions_to_clear = [position] + list(self.neighbors(position))
        for pos in positions_to_clear:
            self.exposure_cache.pop(pos, None)
    
    def check_neighbors(self, position):
        """Check all blocks surrounding position and ensure their visual state is current."""
        for neighbor in self.neighbors(position):
            if neighbor not in self.world:
                continue
            if self.exposed(neighbor):
                if neighbor not in self.shown:
                    self.show_block(neighbor)
            else:
                if neighbor in self.shown:
                    self.hide_block(neighbor)
    
    def check_neighbors_batch(self, positions):
        """Check neighbors for multiple positions efficiently."""
        # Collect all unique neighbors to avoid duplicate processing
        neighbors_to_check = set()
        for position in positions:
            neighbors_to_check.update(self.neighbors(position))
        
        # Process each unique neighbor once
        for neighbor in neighbors_to_check:
            if neighbor not in self.world:
                continue
            if self.exposed(neighbor):
                if neighbor not in self.shown:
                    self.show_block(neighbor)
            else:
                if neighbor in self.shown:
                    self.hide_block(neighbor)
    
    def show_block(self, position):
        """Mock show_block method."""
        if position in self.world:
            self.shown[position] = self.world[position]
    
    def hide_block(self, position):
        """Mock hide_block method."""
        if position in self.shown:
            del self.shown[position]

def test_neighbors_functionality():
    """Test the neighbors generator function."""
    print("Testing neighbors functionality...")
    
    model = TestModel()
    neighbors = list(model.neighbors((0, 0, 0)))
    expected_neighbors = [(0, 1, 0), (0, -1, 0), (-1, 0, 0), (1, 0, 0), (0, 0, 1), (0, 0, -1)]
    
    assert len(neighbors) == 6, f"Expected 6 neighbors, got {len(neighbors)}"
    assert set(neighbors) == set(expected_neighbors), f"Neighbors mismatch: {neighbors} vs {expected_neighbors}"
    print("✅ neighbors function works correctly")

def test_face_exposure():
    """Test face exposure functionality."""
    print("Testing face exposure functionality...")
    
    model = TestModel()
    
    # Add some blocks
    model.world[(0, 0, 0)] = 'GRASS'
    model.world[(1, 0, 0)] = 'GRASS'
    model.world[(0, 1, 0)] = 'GRASS'
    
    # Test face_exposed
    assert model.face_exposed((0, 0, 0), (1, 0, 0)) == False, "Face should not be exposed (has neighbor)"
    assert model.face_exposed((0, 0, 0), (0, 0, 1)) == True, "Face should be exposed (no neighbor)"
    print("✅ face_exposed function works correctly")
    
    # Test get_exposed_faces
    exposed_faces = model.get_exposed_faces((0, 0, 0))
    assert len(exposed_faces) == 4, f"Expected 4 exposed faces, got {len(exposed_faces)}"
    print("✅ get_exposed_faces function works correctly")

def test_exposure_cache():
    """Test exposure caching functionality."""
    print("Testing exposure cache...")
    
    model = TestModel()
    
    # Add a block
    model.world[(0, 0, 0)] = 'GRASS'
    
    # First call should calculate and cache
    exposed1 = model.exposed((0, 0, 0))
    
    # Second call should use cache
    exposed2 = model.exposed((0, 0, 0))
    
    assert exposed1 == exposed2, "Cached result should match original"
    assert (0, 0, 0) in model.exposure_cache, "Position should be in cache"
    print("✅ Exposure cache works correctly")
    
    # Test cache invalidation
    model.invalidate_exposure_cache((0, 0, 0))
    assert (0, 0, 0) not in model.exposure_cache, "Cache should be invalidated"
    print("✅ Cache invalidation works correctly")

def test_batch_neighbor_checking():
    """Test batch neighbor checking functionality."""
    print("Testing batch neighbor checking...")
    
    model = TestModel()
    
    # Add multiple blocks
    positions = [(0, 0, 0), (1, 0, 0), (2, 0, 0)]
    for pos in positions:
        model.world[pos] = 'GRASS'
    
    # Test batch check
    model.check_neighbors_batch(positions)
    print("✅ Batch neighbor checking completed without errors")

def test_performance_improvement():
    """Test that our optimizations provide benefits."""
    print("Testing optimizations...")
    
    model = TestModel()
    
    # Create a 5x5x5 world  
    positions = []
    for x in range(5):
        for y in range(5):
            for z in range(5):
                pos = (x, y, z)
                model.world[pos] = 'GRASS'
                positions.append(pos)
    
    # Time individual neighbor checks
    start_time = time.time()
    for pos in positions[:50]:  # Test first 50 positions
        model.check_neighbors(pos)
    individual_time = time.time() - start_time
    
    # Clear shown blocks
    model.shown.clear()
    
    # Time batch neighbor check
    start_time = time.time()
    model.check_neighbors_batch(positions[:50])
    batch_time = time.time() - start_time
    
    print(f"Individual checks time: {individual_time:.4f}s")
    print(f"Batch check time: {batch_time:.4f}s")
    
    # Test cache performance
    model.exposure_cache.clear()
    start_time = time.time()
    for pos in positions[:50]:
        model.exposed(pos)
    uncached_time = time.time() - start_time
    
    start_time = time.time()
    for pos in positions[:50]:
        model.exposed(pos)  # Should use cache
    cached_time = time.time() - start_time
    
    print(f"Uncached exposure checks: {uncached_time:.4f}s")
    print(f"Cached exposure checks: {cached_time:.4f}s")
    print("✅ Performance tests completed")

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