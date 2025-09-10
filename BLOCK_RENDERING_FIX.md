# Block Rendering Fix

## Issue
Players reported that "la connection se fait, mais je ne vois rien comme blocks, meme si les positions evoluent en fonction de ce que j'utilisees comme bouton" (connection works, but no blocks visible, even though position changes with button input).

## Root Causes
1. **Incorrect Block Geometry**: Block faces were positioned at distance 1.0 from center instead of 0.5, creating 2x2x2 cubes instead of 1x1x1 cubes. This caused overlapping faces and rendering artifacts.

2. **World Data Too Large**: Server was attempting to send 75MB+ of world data in a single WebSocket message, which exceeded the 1MB default limit and prevented clients from receiving any block data.

## Fix Details

### Block Geometry Fix (client.py)
```python
# OLD (incorrect) - created 2x2x2 cubes
faces = [
    ((0, 0, 1), (0, 0, 0)),     # front at distance 1.0
    ((0, 0, -1), (0, 180, 0)),  # back at distance 1.0
    ...
]

# NEW (correct) - creates 1x1x1 cubes  
faces = [
    ((0, 0, 0.5), (0, 0, 0)),    # front at distance 0.5
    ((0, 0, -0.5), (0, 180, 0)), # back at distance 0.5
    ...
]
```

Also added proper depth testing:
```python
self.render.setDepthTest(True)
self.render.setDepthWrite(True)
```

### World Data Transfer Fix (server.py)
Limited world data to prevent oversized messages:
```python
# NEW: Send only blocks within 32-block radius, max 1000 blocks
radius = 32
max_blocks = 1000
# Results in ~300KB messages instead of 75MB
```

## Verification
Run `python3 verify_fix.py` to test the fix. All tests should pass and confirm:
- ✅ Server connection working
- ✅ 1000 blocks received in ~300KB (manageable size)
- ✅ Block geometry fixed
- ✅ Depth testing enabled

## Result
Blocks should now be properly visible in the client with correct 1x1x1 geometry and manageable data transfer sizes.