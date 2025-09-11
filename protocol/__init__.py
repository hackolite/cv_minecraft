"""
Protocol package for Minecraft-like client-server communication
Inspired by pyCraft architecture for robust packet-based communication
"""

from .packets import *
from .connection import Connection
from .auth import AuthManager

__all__ = ['Connection', 'AuthManager']