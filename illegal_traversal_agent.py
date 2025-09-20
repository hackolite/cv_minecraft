#!/usr/bin/env python3
"""
Agent serveur de détection de traversée illégale de blocs.

Cet agent surveille les mouvements des joueurs et détecte si une nouvelle position
se trouve à l'intérieur d'un bloc solide, indiquant une traversée non souhaitée.
"""

import logging
from datetime import datetime
from typing import Dict, Tuple, Optional
from minecraft_physics import UnifiedCollisionManager

# Logger spécialisé pour la détection de traversée illégale
traversal_logger = logging.getLogger('illegal_traversal')


class IllegalBlockTraversalAgent:
    """
    Agent de détection de traversée illégale de blocs.
    
    Surveille chaque mouvement de joueur et détecte les traversées non souhaitées
    de blocs solides. Fournit un logging détaillé et recommande la déconnexion
    du client en cas de violation.
    """
    
    def __init__(self, world_blocks: Dict[Tuple[int, int, int], str]):
        """
        Initialise l'agent avec le monde de blocs.
        
        Args:
            world_blocks: Dictionnaire des blocs du monde {position: type}
        """
        self.collision_manager = UnifiedCollisionManager(world_blocks)
        self.logger = traversal_logger
        
    def check_traversal(self, player_id: str, player_name: Optional[str], 
                       old_position: Tuple[float, float, float],
                       new_position: Tuple[float, float, float]) -> bool:
        """
        Vérifie si le mouvement constitue une traversée illégale de bloc.
        
        Args:
            player_id: Identifiant unique du joueur
            player_name: Nom du joueur (peut être None)
            old_position: Ancienne position (x, y, z)
            new_position: Nouvelle position (x, y, z)
            
        Returns:
            True si une traversée illégale est détectée, False sinon
        """
        # Vérifier si la nouvelle position est dans un bloc solide
        if self.collision_manager.check_block_collision(new_position):
            self._log_illegal_traversal(player_id, player_name, old_position, new_position)
            return True
            
        return False
    
    def _log_illegal_traversal(self, player_id: str, player_name: Optional[str],
                              old_position: Tuple[float, float, float],
                              new_position: Tuple[float, float, float]) -> None:
        """
        Enregistre les détails de la traversée illégale dans les logs.
        
        Args:
            player_id: Identifiant unique du joueur
            player_name: Nom du joueur
            old_position: Ancienne position
            new_position: Nouvelle position
        """
        # Trouver le bloc qui a été traversé
        block_info = self._get_traversed_block_info(new_position)
        
        # Format de timestamp requis
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
        
        # Nom d'affichage du joueur
        display_name = player_name or "Unknown"
        
        # Log principal d'avertissement
        self.logger.warning(
            f"🚨 ILLEGAL BLOCK TRAVERSAL - Player {display_name} ({player_id}) "
            f"traversed solid block {block_info['position']}"
        )
        
        # Logs d'information détaillée
        self.logger.info(f"   Old position: {old_position}")
        self.logger.info(f"   New position: {new_position}")
        self.logger.info(f"   Block type: {block_info['type']}")
        
    def _get_traversed_block_info(self, position: Tuple[float, float, float]) -> Dict[str, any]:
        """
        Obtient les informations sur le bloc traversé.
        
        Args:
            position: Position du joueur
            
        Returns:
            Dictionnaire avec les infos du bloc {position: tuple, type: str}
        """
        px, py, pz = position
        
        # Dimensions du joueur (same as in UnifiedCollisionManager)
        from minecraft_physics import PLAYER_WIDTH, PLAYER_HEIGHT
        largeur = PLAYER_WIDTH
        hauteur = PLAYER_HEIGHT
        profondeur = PLAYER_WIDTH
        
        # Calculer les limites de voxel
        import math
        xmin = int(math.floor(px - largeur / 2))
        xmax = int(math.floor(px + largeur / 2))
        ymin = int(math.floor(py))
        ymax = int(math.floor(py + hauteur))
        zmin = int(math.floor(pz - profondeur / 2))
        zmax = int(math.floor(pz + profondeur / 2))
        
        # Trouver le premier bloc solide dans la région
        for x in range(xmin, xmax + 1):
            for y in range(ymin, ymax + 1):
                for z in range(zmin, zmax + 1):
                    if (x, y, z) in self.collision_manager.world_blocks:
                        block_type = self.collision_manager.world_blocks[(x, y, z)]
                        if block_type != "air":  # Bloc solide trouvé
                            return {
                                'position': (x, y, z),
                                'type': block_type
                            }
        
        # Fallback - ne devrait pas arriver si check_block_collision a retourné True
        return {
            'position': (int(px), int(py), int(pz)),
            'type': 'unknown'
        }
    
    def log_disconnection(self, player_id: str, player_name: Optional[str]) -> None:
        """
        Enregistre la déconnexion du joueur pour traversée illégale.
        
        Args:
            player_id: Identifiant unique du joueur
            player_name: Nom du joueur
        """
        display_name = player_name or "Unknown"
        self.logger.info(f"Player {display_name} ({player_id}) disconnected for illegal block traversal.")