"""
Authentication and session management
Inspired by pyCraft's authentication flow
"""

import hashlib
import time
import uuid
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class PlayerSession:
    """Player session data"""
    uuid: str
    username: str
    created_at: float
    last_seen: float
    authenticated: bool = False
    properties: Dict = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}
    
    def is_expired(self, timeout: float = 3600) -> bool:
        """Check if session is expired"""
        return time.time() - self.last_seen > timeout
    
    def update_last_seen(self):
        """Update last seen timestamp"""
        self.last_seen = time.time()


class AuthManager:
    """
    Authentication manager inspired by pyCraft
    Handles player authentication and session management
    """
    
    def __init__(self, online_mode: bool = False, session_timeout: float = 3600):
        self.online_mode = online_mode
        self.session_timeout = session_timeout
        self.sessions: Dict[str, PlayerSession] = {}
        self.username_to_uuid: Dict[str, str] = {}
        
        # Server authentication
        self.server_id = ""
        self.verify_token = b""
        
    def generate_player_uuid(self, username: str) -> str:
        """Generate a UUID for a player (offline mode)"""
        if self.online_mode:
            # In online mode, UUID would come from Mojang
            raise NotImplementedError("Online mode UUID generation not implemented")
        else:
            # Offline mode: generate UUID from username
            namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # UUID namespace
            player_uuid = str(uuid.uuid5(namespace, username))
            return player_uuid
    
    def create_session(self, username: str, provided_uuid: str = None) -> PlayerSession:
        """Create a new player session"""
        # Clean username
        username = username.strip()
        if not username or len(username) > 16:
            raise ValueError("Invalid username")
        
        # Generate or validate UUID
        if provided_uuid:
            player_uuid = provided_uuid
        else:
            player_uuid = self.generate_player_uuid(username)
        
        # Check if session already exists
        if player_uuid in self.sessions:
            session = self.sessions[player_uuid]
            session.update_last_seen()
            logger.info(f"Reusing existing session for {username} ({player_uuid})")
            return session
        
        # Create new session
        session = PlayerSession(
            uuid=player_uuid,
            username=username,
            created_at=time.time(),
            last_seen=time.time(),
            authenticated=not self.online_mode  # Auto-authenticate in offline mode
        )
        
        self.sessions[player_uuid] = session
        self.username_to_uuid[username.lower()] = player_uuid
        
        logger.info(f"Created new session for {username} ({player_uuid})")
        return session
    
    def get_session(self, player_uuid: str) -> Optional[PlayerSession]:
        """Get a player session by UUID"""
        session = self.sessions.get(player_uuid)
        if session and not session.is_expired(self.session_timeout):
            session.update_last_seen()
            return session
        elif session:
            # Session expired, remove it
            self.remove_session(player_uuid)
        return None
    
    def get_session_by_username(self, username: str) -> Optional[PlayerSession]:
        """Get a player session by username"""
        player_uuid = self.username_to_uuid.get(username.lower())
        if player_uuid:
            return self.get_session(player_uuid)
        return None
    
    def remove_session(self, player_uuid: str) -> None:
        """Remove a player session"""
        session = self.sessions.pop(player_uuid, None)
        if session:
            # Remove from username mapping
            self.username_to_uuid.pop(session.username.lower(), None)
            logger.info(f"Removed session for {session.username} ({player_uuid})")
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions"""
        expired_uuids = []
        for player_uuid, session in self.sessions.items():
            if session.is_expired(self.session_timeout):
                expired_uuids.append(player_uuid)
        
        for player_uuid in expired_uuids:
            self.remove_session(player_uuid)
        
        if expired_uuids:
            logger.info(f"Cleaned up {len(expired_uuids)} expired sessions")
        
        return len(expired_uuids)
    
    def authenticate_player(self, username: str, server_hash: str = None) -> Tuple[bool, str, PlayerSession]:
        """
        Authenticate a player
        Returns: (success, message, session)
        """
        try:
            if self.online_mode:
                # Online mode authentication (would contact Mojang servers)
                return self._authenticate_online(username, server_hash)
            else:
                # Offline mode authentication
                return self._authenticate_offline(username)
                
        except Exception as e:
            logger.error(f"Authentication error for {username}: {e}")
            return False, f"Authentication failed: {str(e)}", None
    
    def _authenticate_offline(self, username: str) -> Tuple[bool, str, PlayerSession]:
        """Authenticate in offline mode"""
        if not username or len(username) > 16:
            return False, "Invalid username", None
        
        # Check for invalid characters
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
        if not all(c in allowed_chars for c in username):
            return False, "Username contains invalid characters", None
        
        # Create or get session
        session = self.create_session(username)
        session.authenticated = True
        
        return True, "Authentication successful", session
    
    def _authenticate_online(self, username: str, server_hash: str) -> Tuple[bool, str, PlayerSession]:
        """Authenticate in online mode (stub implementation)"""
        # This would involve:
        # 1. Generating a server hash
        # 2. Having the client authenticate with Mojang
        # 3. Verifying the authentication with Mojang's session servers
        # 4. Getting the player's UUID and properties from Mojang
        
        # For now, just return failure
        return False, "Online mode authentication not implemented", None
    
    def generate_server_hash(self, shared_secret: bytes, public_key: bytes) -> str:
        """Generate server hash for online mode authentication"""
        sha1 = hashlib.sha1()
        sha1.update(self.server_id.encode('ascii'))
        sha1.update(shared_secret)
        sha1.update(public_key)
        
        # Minecraft uses a special hex format
        hash_bytes = sha1.digest()
        negative = hash_bytes[0] & 0x80
        
        if negative:
            # Two's complement
            hash_bytes = bytearray(hash_bytes)
            for i in range(len(hash_bytes)):
                hash_bytes[i] = ~hash_bytes[i]
            
            # Add 1
            carry = 1
            for i in range(len(hash_bytes) - 1, -1, -1):
                hash_bytes[i] += carry
                if hash_bytes[i] > 255:
                    hash_bytes[i] = hash_bytes[i] & 0xFF
                    carry = 1
                else:
                    carry = 0
                    break
        
        # Convert to hex
        hex_str = hash_bytes.hex()
        
        # Remove leading zeros
        hex_str = hex_str.lstrip('0')
        
        if negative:
            hex_str = '-' + hex_str
        
        return hex_str or '0'
    
    def get_online_players(self) -> int:
        """Get number of online players"""
        return len([s for s in self.sessions.values() 
                   if not s.is_expired(self.session_timeout)])
    
    def get_player_list(self) -> list:
        """Get list of online players"""
        players = []
        for session in self.sessions.values():
            if not session.is_expired(self.session_timeout):
                players.append({
                    'uuid': session.uuid,
                    'username': session.username,
                    'authenticated': session.authenticated,
                    'last_seen': session.last_seen
                })
        return players