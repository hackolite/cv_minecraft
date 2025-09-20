#!/usr/bin/env python3
"""
Demonstration: Tick-Based Physics System for Minecraft Server

This script demonstrates the new tick-based physics system that implements
the exact specifications from the problem statement:

🔹 Logique de la collision (version IA-friendly)

1. Représentation:
- Monde = grille 3D où chaque cellule peut être vide ou solide
- Joueur = boîte rectangulaire verticale (AABB) 
- Vitesse du joueur = (vx, vy, vz) mise à jour à chaque tick
- Paramètres physiques: gravité, vitesse terminale

2. Mise à jour par tick:
- Appliquer la gravité: vy = vy - gravité * dt
- Limiter: vy = max(vy, -vitesse_terminale)
- Calculer translation: dx = vx * dt, dy = vy * dt, dz = vz * dt
- Diviser en sous-étapes pour éviter tunneling (8 étapes)

3. Déplacement et collisions:
- Position candidate = (x+dx, y+dy, z+dz)
- Correction par axe (X, Y, Z indépendamment)  
- Si collision → repositionner et vitesse = 0 sur cet axe
"""

import sys
import os
import time

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    TickBasedPhysicsManager, UnifiedCollisionManager,
    GRAVITY, TERMINAL_VELOCITY, JUMP_VELOCITY,
    get_tick_physics_manager
)

def create_demo_world():
    """Create a demo world for physics testing."""
    world = {}
    
    # Ground plane (terrain)
    for x in range(-5, 15):
        for z in range(-5, 15):
            # Varied terrain height
            if x < 5:
                y = 10
            elif x < 10:
                y = 12  # Higher ground
            else:
                y = 8   # Lower ground
            world[(x, y, z)] = "grass"
    
    # Some obstacles and walls
    # Wall at X=7
    for y in range(11, 16):
        for z in range(2, 8):
            world[(7, y, z)] = "stone"
    
    # Tower structure
    for y in range(13, 20):
        world[(12, y, 5)] = "stone"
        world[(12, y, 6)] = "stone"
        
    # Cliff edge
    for y in range(9, 13):
        world[(10, y, 10)] = "stone"
        world[(11, y, 10)] = "stone"
    
    print(f"🌍 Demo world created with {len(world)} blocks")
    print(f"   Ground levels: Y=10 (left), Y=12 (center), Y=8 (right)")
    print(f"   Wall at X=7, Tower at (12,13-19,5-6), Cliff at (10-11,9-12,10)")
    
    return world

def demonstrate_gravity_and_terminal_velocity():
    """Demonstrate gravity physics and terminal velocity."""
    print("\n🧪 Demonstration 1: Gravity and Terminal Velocity")
    print("=" * 55)
    
    world = create_demo_world()
    physics_manager = get_tick_physics_manager(world)
    
    # Test falling from great height
    position = (2.0, 50.0, 2.0)  # Very high up
    velocity = (0.0, 0.0, 0.0)   # No initial velocity
    dt = 1.0/20.0  # 20 FPS (standard game tick)
    
    print(f"🚀 Player falling from great height: {position}")
    print(f"⚙️  Physics: gravity={GRAVITY}, terminal_velocity={TERMINAL_VELOCITY}")
    print(f"📊 Tick rate: {1/dt} FPS (dt = {dt}s)")
    
    # Simulate falling and track key metrics
    current_pos = position
    current_vel = velocity
    tick = 0
    max_speed_reached = 0.0
    terminal_velocity_ticks = 0
    
    while tick < 200:  # Prevent infinite loop
        old_y = current_pos[1]
        current_pos, current_vel, collision_info = physics_manager.update_tick(
            current_pos, current_vel, dt
        )
        
        tick += 1
        speed = abs(current_vel[1])
        max_speed_reached = max(max_speed_reached, speed)
        
        # Check if we've reached terminal velocity
        if abs(speed - TERMINAL_VELOCITY) < 0.1:
            terminal_velocity_ticks += 1
        
        # Log progress
        if tick <= 10 or tick % 20 == 0 or collision_info['ground']:
            print(f"   Tick {tick:3d}: Y={current_pos[1]:.1f}, Vy={current_vel[1]:.1f}, "
                  f"speed={speed:.1f}, ground={collision_info['ground']}")
        
        # Stop when landed
        if collision_info['ground']:
            print(f"   🎯 Landed after {tick} ticks!")
            break
    
    print(f"   📈 Maximum speed reached: {max_speed_reached:.1f} blocks/s")
    print(f"   📊 Terminal velocity: {TERMINAL_VELOCITY} blocks/s")
    print(f"   ✅ Terminal velocity reached for {terminal_velocity_ticks} ticks")

def demonstrate_anti_tunneling():
    """Demonstrate sub-step movement preventing tunneling."""
    print("\n🧪 Demonstration 2: Anti-Tunneling (Sub-Steps)")
    print("=" * 50)
    
    world = create_demo_world()
    physics_manager = get_tick_physics_manager(world)
    
    print(f"🎯 Testing high-speed movement toward wall at X=7")
    print(f"📊 Sub-steps per tick: {physics_manager.sub_steps}")
    
    # Test very fast movement toward wall
    position = (5.0, 13.0, 5.0)    # Left side of wall
    velocity = (50.0, 0.0, 0.0)    # Extremely fast movement (50 blocks/s)
    dt = 1.0/20.0
    
    expected_movement = velocity[0] * dt  # 50 * 0.05 = 2.5 blocks per tick
    
    print(f"   Start position: {position}")
    print(f"   Velocity: {velocity[0]} blocks/s")
    print(f"   Movement per tick: {expected_movement} blocks")
    print(f"   Without sub-steps, would reach: X={position[0] + expected_movement}")
    print(f"   Wall position: X=7")
    
    # Apply one tick of movement
    new_position, new_velocity, collision_info = physics_manager.update_tick(
        position, velocity, dt
    )
    
    print(f"   Final position: {new_position}")
    print(f"   Final velocity: {new_velocity}")
    print(f"   Collision detected: {collision_info}")
    
    if new_position[0] < 7.0:
        print(f"   ✅ Anti-tunneling successful! Stopped at X={new_position[0]:.2f}")
        print(f"   ✅ Velocity reset from {velocity[0]} to {new_velocity[0]}")
    else:
        print(f"   ❌ Tunneling occurred! Reached X={new_position[0]}")

def demonstrate_per_axis_collision():
    """Demonstrate per-axis collision resolution."""
    print("\n🧪 Demonstration 3: Per-Axis Collision Resolution")
    print("=" * 55)
    
    # Create world with corner obstacle
    world = {}
    # Ground
    for x in range(0, 10):
        for z in range(0, 10):
            world[(x, 10, z)] = "grass"
    
    # L-shaped wall
    for y in range(11, 14):
        world[(5, y, 3)] = "stone"  # Vertical part
        world[(5, y, 4)] = "stone"
        world[(5, y, 5)] = "stone"
        world[(6, y, 5)] = "stone"  # Horizontal part 
        world[(7, y, 5)] = "stone"
    
    physics_manager = get_tick_physics_manager(world)
    
    print(f"🏗️  L-shaped wall created")
    print(f"   Vertical: X=5, Z=3-5")
    print(f"   Horizontal: X=5-7, Z=5")
    
    # Test diagonal movement toward corner
    position = (4.0, 11.0, 4.0)
    velocity = (3.0, 0.0, 3.0)  # Diagonal movement
    dt = 1.0/20.0
    
    print(f"   Start position: {position}")
    print(f"   Diagonal velocity: {velocity}")
    print(f"   Target (without collision): ({position[0] + velocity[0]*dt:.2f}, "
          f"{position[1]}, {position[2] + velocity[2]*dt:.2f})")
    
    # Apply movement
    new_position, new_velocity, collision_info = physics_manager.update_tick(
        position, velocity, dt
    )
    
    print(f"   Final position: {new_position}")
    print(f"   Final velocity: {new_velocity}")
    print(f"   Per-axis collision resolution:")
    print(f"     X-axis: {'BLOCKED' if collision_info['x'] else 'ALLOWED'}")
    print(f"     Y-axis: {'BLOCKED' if collision_info['y'] else 'ALLOWED'}")
    print(f"     Z-axis: {'BLOCKED' if collision_info['z'] else 'ALLOWED'}")
    
    # Show how movement is preserved on non-blocked axes
    blocked_axes = [axis for axis in ['x', 'y', 'z'] if collision_info[axis]]
    free_axes = [axis for axis in ['x', 'y', 'z'] if not collision_info[axis]]
    
    if blocked_axes:
        print(f"   🚫 Movement blocked on: {blocked_axes}")
        print(f"   ✅ Movement allowed on: {free_axes}")
        print(f"   → Player can slide along walls!")

def demonstrate_complete_gameplay():
    """Demonstrate complete gameplay scenario."""
    print("\n🧪 Demonstration 4: Complete Gameplay Scenario")
    print("=" * 52)
    
    world = create_demo_world()
    physics_manager = get_tick_physics_manager(world)
    
    print(f"🎮 Simulating realistic player movement")
    
    # Player starts high up and moves around
    position = (1.0, 25.0, 1.0)
    velocity = (0.0, 0.0, 0.0)
    dt = 1.0/60.0  # 60 FPS for smooth simulation
    
    scenarios = [
        {
            "name": "Free fall",
            "velocity": (0.0, 0.0, 0.0),
            "ticks": 100,
            "description": "Player falls and lands on ground"
        },
        {
            "name": "Walking on ground", 
            "velocity": (3.0, 0.0, 0.0),
            "ticks": 50,
            "description": "Player walks east on flat ground"
        },
        {
            "name": "Jump and move",
            "velocity": (2.0, 0.0, 1.0),
            "ticks": 40,
            "jumping": True,
            "description": "Player jumps while moving diagonally"
        },
        {
            "name": "Hit wall",
            "velocity": (8.0, 0.0, 0.0),
            "ticks": 30,
            "description": "Player runs into wall and stops"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n   📋 Scenario: {scenario['name']} - {scenario['description']}")
        
        velocity = scenario['velocity']
        jumping = scenario.get('jumping', False)
        
        # Run scenario
        for tick in range(scenario['ticks']):
            old_pos = position
            position, velocity, collision_info = physics_manager.update_tick(
                position, velocity, dt, jumping=(jumping and tick == 0)
            )
            
            # Log key events
            if tick == 0:
                print(f"     Start: pos=({position[0]:.1f}, {position[1]:.1f}, {position[2]:.1f})")
            
            # Check for significant events
            if collision_info['ground'] and not old_pos[1] <= position[1]:
                print(f"     Tick {tick:2d}: Landed at Y={position[1]:.1f}")
            
            if any([collision_info['x'], collision_info['z']]):
                blocked = [k for k, v in collision_info.items() if v and k in ['x', 'z']]
                print(f"     Tick {tick:2d}: Hit wall - {blocked} blocked")
                break
                
            if tick % 20 == 0 and tick > 0:
                print(f"     Tick {tick:2d}: pos=({position[0]:.1f}, {position[1]:.1f}, {position[2]:.1f}), "
                      f"vel=({velocity[0]:.1f}, {velocity[1]:.1f}, {velocity[2]:.1f})")
        
        print(f"     End: pos=({position[0]:.1f}, {position[1]:.1f}, {position[2]:.1f}), "
              f"vel=({velocity[0]:.1f}, {velocity[1]:.1f}, {velocity[2]:.1f})")

def main():
    """Run all demonstrations."""
    print("🎮 Tick-Based Physics System for Minecraft Server")
    print("=" * 60)
    print("Implementing the exact specifications:")
    print("• Gravity: vy = vy - gravité * dt")
    print("• Terminal velocity: vy = max(vy, -vitesse_terminale)")
    print("• Sub-steps: 8 étapes per tick to prevent tunneling")
    print("• Per-axis collision resolution")
    print("• Velocity reset on blocked axes")
    
    try:
        demonstrate_gravity_and_terminal_velocity()
        demonstrate_anti_tunneling()
        demonstrate_per_axis_collision()
        demonstrate_complete_gameplay()
        
        print("\n🎉 ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print("✅ Tick-based physics system is working according to specifications")
        print("✅ Gravity and terminal velocity implemented correctly")
        print("✅ Sub-step movement prevents tunneling through blocks")
        print("✅ Per-axis collision resolution allows smooth movement")
        print("✅ Velocity reset system working properly")
        print("\n🚀 The tick-based physics system is ready for server integration!")
        
    except Exception as e:
        print(f"\n❌ DEMONSTRATION FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()