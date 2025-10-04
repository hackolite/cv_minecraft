# Block Metadata and Block ID System

## Overview

This implementation adds comprehensive block metadata support to the Minecraft server, including collision attributes and block IDs for all blocks. This allows for more sophisticated block queries and better organization of different block types.

## Changes Made

### 1. Block Data Structure

**Before:**
- Blocks stored as: `position -> block_type_string`

**After:**
- Blocks stored as: `position -> block_data_dict`
- Block data dict contains:
  - `type`: Block type (string)
  - `collision`: Whether the block has collision (boolean)
  - `block_id`: Unique identifier for camera and user blocks (string or None)

### 2. New Features

#### Collision Attribute
All blocks now have a `collision` attribute that indicates whether they block player movement:
- **Collision enabled**: grass, sand, brick, stone, wood, leaf, camera, user
- **No collision**: water, air

#### Block ID System
- All blocks have a `block_id` field
- Only **camera** and **user** blocks have populated block_ids
- Camera blocks: auto-assigned IDs like `camera_0`, `camera_1`, etc.
- User blocks: assigned using player_id (e.g., player's UUID)

#### Block ID Mapping
- Server maintains a `block_id_map` dictionary: `block_id -> position`
- Enables fast lookup of block position by ID
- Automatically updated when blocks are added/removed/moved

### 3. New Block Type: USER

Added a new block type `BlockType.USER` to represent player positions as blocks in the world:
- User blocks are created when players join
- Updated when players move
- Removed when players disconnect
- Have collision enabled
- Include player's ID as block_id

### 4. Query Enhancements

#### Query Blocks by Block ID
The `get_blocks_list` service now supports querying from a block's perspective using its `block_id`:

```json
{
  "type": "get_blocks_list",
  "data": {
    "query_type": "view",
    "block_id": "camera_0",      // Query from this block's position
    "rotation": [0, 0],          // Viewing direction
    "view_distance": 30.0        // Distance to see
  }
}
```

Previously, you had to provide explicit coordinates:
```json
{
  "type": "get_blocks_list",
  "data": {
    "query_type": "view",
    "position": [x, y, z],       // Had to know exact position
    "rotation": [0, 0],
    "view_distance": 30.0
  }
}
```

#### Metadata in Responses
All block query responses now include complete metadata:

```json
{
  "type": "blocks_list",
  "data": {
    "blocks": [
      {
        "position": [69, 102, 64],
        "block_type": "camera",
        "block_id": "camera_0",
        "collision": true,
        "distance": 10.5        // For view queries
      },
      {
        "position": [70, 100, 65],
        "block_type": "grass",
        "block_id": null,       // Regular blocks don't have IDs
        "collision": true
      },
      {
        "position": [71, 100, 66],
        "block_type": "water",
        "block_id": null,
        "collision": false      // Water has no collision
      }
    ]
  }
}
```

### 5. Backward Compatibility

The system maintains backward compatibility:
- Collision system handles both old string format and new dict format
- Helper functions `get_block_type_from_data()` and `has_block_collision()` abstract the difference
- Existing code continues to work without modification

## API Usage Examples

### Get Camera Blocks with Metadata

```python
cameras_request = {"type": "get_cameras_list", "data": {}}
# Response includes block_id and collision:
# {
#   "cameras": [
#     {
#       "position": [69, 102, 64],
#       "block_type": "camera",
#       "block_id": "camera_0",
#       "collision": true
#     }
#   ]
# }
```

### Query Blocks from Camera Perspective

```python
blocks_request = {
    "type": "get_blocks_list",
    "data": {
        "query_type": "view",
        "block_id": "camera_0",  # Use camera's block_id
        "rotation": [0, 0],
        "view_distance": 30.0
    }
}
# Returns all blocks visible from camera_0's position
```

### Query Blocks from User Perspective

```python
blocks_request = {
    "type": "get_blocks_list",
    "data": {
        "query_type": "view",
        "block_id": "user_player_uuid",  # Use player's ID
        "rotation": [45, 0],
        "view_distance": 20.0
    }
}
# Returns all blocks visible from the user's position
```

### Get Blocks in Region with Metadata

```python
blocks_request = {
    "type": "get_blocks_list",
    "data": {
        "query_type": "region",
        "center": [64, 100, 64],
        "radius": 50.0
    }
}
# All blocks include collision and block_id fields
```

## Technical Implementation

### Server-Side Changes

1. **server.py**:
   - Added `create_block_data()` helper function
   - Added `get_block_collision()` helper function
   - Updated `GameWorld` class with `block_id_map`
   - Added `add_user_block()` and `remove_user_block()` methods
   - Updated all block retrieval methods to include metadata
   - Enhanced `_handle_get_blocks_list()` to support block_id queries

2. **protocol.py**:
   - Added `BlockType.USER` constant

3. **minecraft_physics.py**:
   - Added `get_block_type_from_data()` helper function
   - Added `has_block_collision()` helper function
   - Updated all collision checks to use helper functions
   - Properly handles both string and dict block data formats

### Testing

Two comprehensive test suites verify the implementation:

1. **test_block_metadata.py**: Unit tests for:
   - Block data creation
   - Collision function
   - Block management with metadata
   - User block management
   - Camera metadata retrieval
   - Block_id query support

2. **test_block_id_integration.py**: Integration tests with running server:
   - Query by block_id functionality
   - Complete metadata in responses
   - Backward compatibility

All tests pass successfully.

## Benefits

1. **Better Organization**: Camera and user blocks can be identified and tracked
2. **Efficient Queries**: Direct lookup by block_id without iterating through positions
3. **Enhanced Metadata**: Collision information enables better game logic
4. **Flexible Queries**: Can query from any block's perspective using its ID
5. **Type Safety**: Explicit collision attribute prevents errors
6. **Future-Proof**: System extensible for additional block metadata

## Migration Notes

For existing code:
- No changes required for basic functionality
- Queries will automatically include new metadata
- Can optionally use block_id for more efficient queries
- Collision detection automatically uses new metadata
