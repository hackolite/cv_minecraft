"""
Cube Manager - Central management for cube instances and port allocation
"""

import socket
import threading
from typing import Set, Optional
import logging

class CubeManager:
    """Central manager for cube instances and port allocation."""
    
    def __init__(self, port_start: int = 8081, port_end: int = 8999):
        """
        Initialize the cube manager.
        
        Args:
            port_start: Starting port for dynamic allocation
            port_end: Ending port for dynamic allocation
        """
        self.port_start = port_start
        self.port_end = port_end
        self.used_ports: Set[int] = set()
        self.reserved_ports: Set[int] = {8080, 8765}  # Reserve main server ports
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
        # Initialize with reserved ports
        self.used_ports.update(self.reserved_ports)
    
    def is_port_available(self, port: int) -> bool:
        """Check if a port is available for use."""
        if port in self.used_ports:
            return False
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                result = sock.connect_ex(('localhost', port))
                return result != 0  # True if port is free
        except Exception:
            return False
    
    def allocate_port(self) -> Optional[int]:
        """
        Allocate an available port dynamically.
        
        Returns:
            Available port number or None if no ports available
        """
        with self.lock:
            for port in range(self.port_start, self.port_end + 1):
                if port not in self.used_ports and self.is_port_available(port):
                    self.used_ports.add(port)
                    self.logger.info(f"Allocated port {port}")
                    return port
            
            self.logger.warning("No available ports in range")
            return None
    
    def release_port(self, port: int):
        """
        Release a previously allocated port.
        
        Args:
            port: Port number to release
        """
        with self.lock:
            if port and port not in self.reserved_ports:
                self.used_ports.discard(port)
                self.logger.info(f"Released port {port}")
    
    def get_used_ports(self) -> Set[int]:
        """Get a copy of all currently used ports."""
        with self.lock:
            return self.used_ports.copy()
    
    def get_available_port_count(self) -> int:
        """Get the number of available ports."""
        with self.lock:
            total_range = self.port_end - self.port_start + 1
            return total_range - len(self.used_ports)

# Global instance
cube_manager = CubeManager()