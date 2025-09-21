# Minecraft Client-Server

This is a modded version of Fogleman's "Minecraft" which has been converted from a monolithic architecture to a client-server architecture for multiplayer support, **and now also includes a standalone version for single-player use**.

Original: https://github.com/fogleman/Minecraft

Video here: https://www.youtube.com/watch?v=S4EUQD9QIzc&lc=z23mubkgxpapjvhot04t1aokgeofqomvondp5x4qnz1abk0h00410

## Architecture Options

This version now offers **two architecture choices**:

### 🌐 Client-Server Architecture (Multiplayer)
- **Server (`server.py`)**: Manages the authoritative game world, handles multiple client connections via WebSockets, processes game logic, and synchronizes state between clients
- **Client (`minecraft_client_fr.py`)**: Handles rendering, user input, and connects to the server for world updates and multiplayer interaction
- **Protocol (`protocol.py`)**: Defines message types and data structures for client-server communication

### 🏠 Standalone Architecture (Single-player)
- **Standalone Client (`minecraft_standalone.py`)**: Complete game running entirely client-side with local world generation, physics, and save/load
- **Standalone GUI (`minecraft_client_standalone.py`)**: Full 3D graphical interface version (requires OpenGL)
- **No Server Required**: All game logic, physics, and world management handled locally

### Key Features

**Client-Server Mode:**
- ✅ **Multiplayer Support**: Multiple players can connect and play together
- ✅ **WebSocket Communication**: Real-time synchronization between clients and server
- ✅ **Chunked World Loading**: Efficient world data transmission in 16x16 chunks
- ✅ **Authoritative Server**: Server manages world state to prevent cheating
- ✅ **Real-time Updates**: Block placement/destruction synchronized across all clients
- ✅ **Player Movement Tracking**: See other players move in real-time

**Standalone Mode:**
- ✅ **No Server Required**: Complete game runs entirely client-side
- ✅ **Local World Generation**: Procedural terrain generation with noise
- ✅ **Client-side Physics**: Full physics engine with collision detection
- ✅ **Save/Load System**: Local world persistence with file-based storage
- ✅ **Text Mode Support**: Command-line interface for testing and headless environments
- ✅ **Offline Play**: Works without internet connection

## How to Run

### 🚀 Easy Launcher (Recommended)

Use the launcher to choose between client-server and standalone modes:

```shell
python3 launcher_minecraft.py
```

The launcher will guide you through the options and handle dependencies automatically.

### 🌐 Client-Server Mode (Multiplayer)

### Prerequisites

```shell
pip install -r requirements.txt
```

### Starting the Game

1. **Start the Server** (in one terminal):
```shell
python3 server.py
```

2. **Start Client(s)** (in separate terminals):
```shell
python3 client.py
```

You can start multiple clients to test multiplayer functionality.

### 🏠 Standalone Mode (Single-player)

**Option 1: GUI Version (requires OpenGL)**
```shell
python3 minecraft_client_standalone.py
```

**Option 2: Text Mode (works anywhere)**
```shell
python3 minecraft_standalone.py --text-mode
```

**Option 3: Generate world and GUI**
```shell
python3 minecraft_standalone.py  # Will attempt GUI, fallback to text
```

### 💻 Standalone Text Mode Commands

When running in text mode, use these commands:
- `help` - Show available commands
- `status` - Display player status
- `move <x> <y> <z>` - Move player by offset
- `tp <x> <y> <z>` - Teleport to position
- `fly` - Toggle flying mode
- `place <type>` - Place block (grass, stone, wood, sand, brick)
- `break` - Destroy targeted block
- `save <filename>` - Save world to file
- `load <filename>` - Load world from file
- `quit` - Exit game

### Controls

**GUI Modes (both client-server and standalone):**
- **ZQSD**: Movement (WASD-like for French keyboards)
- **Mouse**: Look around
- **Space**: Jump
- **Left Click**: Destroy block
- **Right Click**: Place block
- **1-5**: Change block type
- **Tab**: Toggle flying mode
- **R**: Sprint
- **Shift**: Crouch
- **Escape**: Release mouse cursor
- **F3**: Toggle debug info
- **F5**: Save world (standalone only)
- **F9**: Load world (standalone only)

**Text Mode (standalone only):**
- Type commands followed by Enter
- See command list above

## Testing

### Test Server Connection
```shell
python3 test_connection.py
```

### Test Multiplayer
```shell
python3 test_multiplayer.py
```

## Original Monolithic Version

The original single-player version is still available in `minecraft.py` and can be run with:
```shell
python3 main.py
```

### Mac

On Mac OS X, you may have an issue with running Pyglet in 64-bit mode. Try running Python in 32-bit mode first:

```shell
arch -i386 python3 server.py  # In one terminal
arch -i386 python3 client.py  # In another terminal
```

If that doesn't work, set Python to run in 32-bit mode by default:

```shell
defaults write com.apple.versioner.python Prefer-32-Bit -bool yes 
```

This assumes you are using the OS X default Python. Works on Lion 10.7 with the default Python 2.7, and may work on other versions too. Please raise an issue if not.
    
Or try Pyglet 1.2 alpha, which supports 64-bit mode:  

```shell
pip install https://pyglet.googlecode.com/files/pyglet-1.2alpha1.tar.gz 
```

### Dependencies Installation

For pip:

- Mac or Linux: install with `sudo easy_install pip` (Mac or Linux) - or (Linux) find a package called something like 'python-pip' in your package manager.
- Windows: [install Distribute then Pip](http://stackoverflow.com/a/12476379/992887) using the linked .MSI installers.

For git:

- Mac: install [Homebrew](http://mxcl.github.com/homebrew/) first, then `brew install git`.
- Windows or Linux: see [Installing Git](http://git-scm.com/book/en/Getting-Started-Installing-Git) from the _Pro Git_ book.

See the [wiki](https://github.com/fogleman/Minecraft/wiki) for this project to install Python, and other tips.

## Architecture Conversion

See `CONVERSION_GUIDE.md` for technical details about the conversion from monolithic to client-server architecture.
