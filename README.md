# Minecraft Client-Server

This is a modded version of Fogleman's "Minecraft" which has been converted from a monolithic architecture to a client-server architecture for multiplayer support.

Original: https://github.com/fogleman/Minecraft

Video here: https://www.youtube.com/watch?v=S4EUQD9QIzc&lc=z23mubkgxpapjvhot04t1aokgeofqomvondp5x4qnz1abk0h00410

## Architecture

This version has been restructured into a **client-server architecture**:

- **Server (`server.py`)**: Manages the authoritative game world, handles multiple client connections via WebSockets, processes game logic, and synchronizes state between clients
- **Client (`client.py`)**: Handles rendering, user input, and connects to the server for world updates and multiplayer interaction
- **Protocol (`protocol.py`)**: Defines message types and data structures for client-server communication

### Key Features

- ✅ **Multiplayer Support**: Multiple players can connect and play together
- ✅ **WebSocket Communication**: Real-time synchronization between clients and server
- ✅ **Chunked World Loading**: Efficient world data transmission in 16x16 chunks
- ✅ **Authoritative Server**: Server manages world state to prevent cheating
- ✅ **Real-time Updates**: Block placement/destruction synchronized across all clients
- ✅ **Player Movement Tracking**: See other players move in real-time
- ✅ **FastAPI Integration**: Abstract client with REST API for programmatic control

## How to Run

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

### Controls

- **ZQSD**: Movement (WASD-like for French keyboards)
- **Mouse**: Look around
- **Space**: Jump
- **Left Click**: Destroy block
- **Right Click**: Place block
- **1-4**: Change block type
- **Tab**: Toggle flying mode
- **R**: Sprint
- **Shift**: Crouch
- **Escape**: Release mouse cursor

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
