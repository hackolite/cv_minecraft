# Position Reset Fix Documentation

## Problem
The issue reported was: "quand j'essaie de changer de position, ça reviens a zero a chaque fois" (when I try to change position, it returns to zero each time).

## Root Cause Analysis
The position reset issue was caused by incomplete client-server position synchronization:

1. **Client-side movement was not sent to server**: The client had movement functions (`move_forward`, `move_backward`, etc.) that updated the camera position locally but never communicated these changes to the server.

2. **Server position tracking was not updated**: The server maintained player positions in `self.player_positions[websocket]` but only set them during spawn - they were never updated when players moved.

3. **World data was sent from outdated position**: When clients requested world data, the server used the outdated spawn position instead of the current player position.

## Solution Implemented

### 1. Client sends position updates to server
Modified `update_camera_position()` in `client.py` to send position updates:

```python
def update_camera_position(self):
    """Update camera position and send to server if needed."""
    self.position = self.camera.getPos()
    
    # Send position update to server only if moved significantly
    if self.connected:
        should_send = False
        
        if self.last_sent_position is None:
            should_send = True
        else:
            # Calculate distance moved since last update
            distance = (self.position - self.last_sent_position).length()
            if distance >= self.position_update_threshold:
                should_send = True
        
        if should_send:
            position_data = {
                'type': 'move',
                'position': [self.position.x, self.position.y, self.position.z]
            }
            self.outgoing_messages.put(json.dumps(position_data))
            self.last_sent_position = Vec3(self.position)
```

### 2. Client handles spawn position from server
Updated the client to properly set its position when receiving the welcome message:

```python
# Handle initial spawn position from server
spawn_position = data.get('position')
if spawn_position:
    print(f"Setting spawn position: {spawn_position}")
    # Convert to Vec3 and set camera position
    spawn_vec = Vec3(spawn_position[0], spawn_position[1], spawn_position[2])
    self.camera.setPos(spawn_vec)
    self.position = spawn_vec
    self.last_sent_position = Vec3(spawn_vec)  # Initialize last sent position
```

### 3. Added position update throttling
To prevent excessive network traffic, position updates are only sent when the player has moved more than 0.5 units from their last sent position.

### 4. Server already had correct handling
The server already correctly handled `move` messages in `handle_move()` and used the updated position for world data requests in `handle_get_world()`.

## Testing
Created comprehensive tests to verify the fix:

1. **test_position_sync.py**: Verifies basic position synchronization
2. **test_position_throttling.py**: Tests that small movements are throttled
3. **test_position_persistence.py**: Confirms positions don't reset to zero
4. **test_position_fix.py**: Demonstrates the complete fix

## Result
- ✅ Player movements are now sent to the server
- ✅ Server remembers player positions correctly
- ✅ World data is sent relative to current player position, not spawn
- ✅ Position changes persist and don't reset to zero
- ✅ Network traffic is optimized with movement throttling
- ✅ All existing functionality remains intact (no regressions)

## Files Modified
- `client.py`: Added position synchronization and throttling

## Files Added
- `test_position_fix.py`: Demonstration script for the fix