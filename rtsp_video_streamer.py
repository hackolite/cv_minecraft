#!/usr/bin/env python3
"""
RTSP Video Streamer for Observer Cameras
Diffuseur vidéo RTSP pour caméras d'observateurs

Ce module implémente le streaming vidéo réel via RTSP pour les caméras d'observateurs.
"""

import asyncio
import socket
import struct
import time
import threading
from typing import Optional, Dict, Any
import logging

from observer_camera import ObserverCamera


class RTSPVideoStream:
    """Stream vidéo RTSP pour une caméra d'observateur."""
    
    def __init__(self, camera: ObserverCamera, session_id: str):
        self.camera = camera
        self.session_id = session_id
        self.is_streaming = False
        self.rtp_socket = None
        self.rtcp_socket = None
        self.client_rtp_port = None
        self.client_rtcp_port = None
        self.server_rtp_port = None
        self.server_rtcp_port = None
        self.sequence_number = 0
        self.timestamp_base = int(time.time() * 90000)  # 90kHz pour video
        self.ssrc = hash(session_id) & 0xFFFFFFFF
        self.streaming_thread = None
        self.logger = logging.getLogger(f"{__name__}.{camera.observer_id}")
        
    def setup_transport(self, client_ports: str) -> Dict[str, Any]:
        """Configure le transport RTP/RTCP."""
        try:
            # Parser les ports client (format: "8000-8001")
            if '-' in client_ports:
                port_parts = client_ports.split('-')
                self.client_rtp_port = int(port_parts[0])
                self.client_rtcp_port = int(port_parts[1])
            else:
                self.client_rtp_port = int(client_ports)
                self.client_rtcp_port = self.client_rtp_port + 1
                
            # Créer les sockets serveur
            self.rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.rtcp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Bind à des ports libres
            self.rtp_socket.bind(('localhost', 0))
            self.rtcp_socket.bind(('localhost', 0))
            
            self.server_rtp_port = self.rtp_socket.getsockname()[1]
            self.server_rtcp_port = self.rtcp_socket.getsockname()[1]
            
            self.logger.info(f"Transport configuré - Client: {self.client_rtp_port}-{self.client_rtcp_port}, "
                           f"Serveur: {self.server_rtp_port}-{self.server_rtcp_port}")
            
            return {
                'client_ports': f"{self.client_rtp_port}-{self.client_rtcp_port}",
                'server_ports': f"{self.server_rtp_port}-{self.server_rtcp_port}"
            }
            
        except Exception as e:
            self.logger.error(f"Erreur configuration transport: {e}")
            return None
            
    def start_streaming(self):
        """Démarre le streaming vidéo."""
        if self.is_streaming or not self.rtp_socket:
            return
            
        self.is_streaming = True
        self.streaming_thread = threading.Thread(target=self._streaming_loop, daemon=True)
        self.streaming_thread.start()
        self.logger.info("Streaming vidéo démarré")
        
    def stop_streaming(self):
        """Arrête le streaming vidéo."""
        self.is_streaming = False
        if self.streaming_thread:
            self.streaming_thread.join(timeout=1.0)
            
        if self.rtp_socket:
            self.rtp_socket.close()
        if self.rtcp_socket:
            self.rtcp_socket.close()
            
        self.logger.info("Streaming vidéo arrêté")
        
    def _streaming_loop(self):
        """Boucle principale de streaming."""
        frame_duration = 1.0 / 30.0  # 30 FPS
        
        while self.is_streaming:
            start_time = time.time()
            
            try:
                # Obtenir le frame le plus récent de la caméra
                frame_data = self.camera.get_latest_frame()
                if frame_data:
                    self._send_rtp_packet(frame_data['data'])
                    
            except Exception as e:
                self.logger.error(f"Erreur streaming: {e}")
                
            # Maintenir le framerate
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_duration - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
                
    def _send_rtp_packet(self, frame_data: bytes):
        """Envoie un paquet RTP avec les données vidéo."""
        try:
            # Créer l'en-tête RTP (12 bytes)
            version = 2
            padding = 0
            extension = 0
            cc = 0  # CSRC count
            marker = 1  # End of frame
            payload_type = 96  # Dynamic payload type for H.264
            
            # Calculer le timestamp
            current_time = int(time.time() * 90000)  # 90kHz
            timestamp = current_time - self.timestamp_base
            
            # Construire l'en-tête RTP
            first_byte = (version << 6) | (padding << 5) | (extension << 4) | cc
            second_byte = (marker << 7) | payload_type
            
            rtp_header = struct.pack('>BBHII',
                                   first_byte,
                                   second_byte,
                                   self.sequence_number & 0xFFFF,
                                   timestamp & 0xFFFFFFFF,
                                   self.ssrc)
            
            # Pour simplifier, on envoie les données JPEG directement
            # Dans une vraie implémentation, il faudrait encoder en H.264
            payload = frame_data[:1400]  # Limiter la taille du paquet
            
            packet = rtp_header + payload
            
            # Envoyer le paquet
            self.rtp_socket.sendto(packet, ('localhost', self.client_rtp_port))
            
            self.sequence_number += 1
            
        except Exception as e:
            self.logger.error(f"Erreur envoi paquet RTP: {e}")


class EnhancedRTSPServer:
    """Serveur RTSP amélioré avec streaming vidéo réel."""
    
    def __init__(self, user, camera: ObserverCamera):
        self.user = user
        self.camera = camera
        self.is_running = False
        self.logger = logging.getLogger(f"{__name__}.{user.name}")
        self.server_socket = None
        self.server_task = None
        self.active_streams: Dict[str, RTSPVideoStream] = {}
        
    async def start(self) -> None:
        """Démarre le serveur RTSP amélioré."""
        if self.is_running:
            return
            
        try:
            # Créer le socket serveur
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('localhost', self.user.rtsp_port))
            self.server_socket.listen(5)
            
            self.is_running = True
            self.logger.info(f"Serveur RTSP amélioré démarré sur {self.user.rtsp_url}")
            
            # Démarrer l'acceptation des connexions
            self.server_task = asyncio.create_task(self._run_server())
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage serveur RTSP amélioré: {e}")
            raise
            
    async def stop(self) -> None:
        """Arrête le serveur RTSP amélioré."""
        if not self.is_running:
            return
            
        self.is_running = False
        
        # Arrêter tous les streams actifs
        for stream in self.active_streams.values():
            stream.stop_streaming()
        self.active_streams.clear()
        
        # Annuler la tâche serveur
        if self.server_task:
            self.server_task.cancel()
            try:
                await self.server_task
            except asyncio.CancelledError:
                pass
        
        # Fermer le socket serveur
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
                
        self.logger.info(f"Serveur RTSP amélioré arrêté pour {self.user.name}")
        
    async def _run_server(self):
        """Exécute le serveur RTSP."""
        import concurrent.futures
        
        def server_thread():
            while self.is_running:
                try:
                    self.server_socket.settimeout(1.0)
                    try:
                        client_socket, addr = self.server_socket.accept()
                        self.logger.info(f"Connexion RTSP de {addr}")
                        
                        # Créer un thread pour gérer ce client
                        client_thread = threading.Thread(
                            target=self._handle_client_sync,
                            args=(client_socket, addr),
                            daemon=True
                        )
                        client_thread.start()
                        
                    except socket.timeout:
                        continue
                        
                except Exception as e:
                    if self.is_running:
                        self.logger.error(f"Erreur serveur RTSP: {e}")
                    break
        
        # Exécuter le serveur dans un thread
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            try:
                await loop.run_in_executor(executor, server_thread)
            except asyncio.CancelledError:
                pass
                
    def _handle_client_sync(self, client_socket, addr):
        """Gère un client RTSP connecté avec streaming vidéo."""
        session_id = None
        stream = None
        
        try:
            client_socket.settimeout(30.0)
            
            while self.is_running:
                try:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                        
                    request = data.decode('utf-8', errors='ignore')
                    self.logger.info(f"Requête RTSP de {addr}: {request.split()[0]} {request.split()[1] if len(request.split()) > 1 else ''}")
                    
                    # Parser la requête
                    lines = request.strip().split('\r\n')
                    if not lines:
                        continue
                        
                    request_line = lines[0]
                    headers = {}
                    
                    for line in lines[1:]:
                        if ':' in line:
                            key, value = line.split(':', 1)
                            headers[key.strip().lower()] = value.strip()
                    
                    cseq = headers.get('cseq', '1')
                    
                    # Gérer les requêtes RTSP
                    if request_line.startswith('OPTIONS'):
                        response = self._create_options_response(cseq)
                    elif request_line.startswith('DESCRIBE'):
                        response = self._create_describe_response(cseq)
                    elif request_line.startswith('SETUP'):
                        session_id = f"session_{self.user.rtsp_port}_{addr[1]}"
                        stream = RTSPVideoStream(self.camera, session_id)
                        self.active_streams[session_id] = stream
                        response = self._create_setup_response(cseq, headers, stream)
                    elif request_line.startswith('PLAY'):
                        if stream:
                            stream.start_streaming()
                        response = self._create_play_response(cseq, session_id)
                    elif request_line.startswith('TEARDOWN'):
                        if stream and session_id in self.active_streams:
                            stream.stop_streaming()
                            del self.active_streams[session_id]
                        response = self._create_teardown_response(cseq)
                        client_socket.send(response.encode())
                        break
                    else:
                        response = self._create_error_response(cseq, '501 Not Implemented')
                    
                    client_socket.send(response.encode())
                    
                except socket.timeout:
                    break
                except Exception as e:
                    self.logger.error(f"Erreur traitement requête de {addr}: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Erreur gestion client {addr}: {e}")
        finally:
            # Nettoyage
            if stream and session_id in self.active_streams:
                stream.stop_streaming()
                del self.active_streams[session_id]
                
            try:
                client_socket.close()
            except:
                pass
            self.logger.info(f"Client RTSP {addr} déconnecté")
            
    def _create_options_response(self, cseq):
        """Crée une réponse OPTIONS."""
        return (
            f"RTSP/1.0 200 OK\r\n"
            f"CSeq: {cseq}\r\n"
            f"Public: OPTIONS, DESCRIBE, SETUP, TEARDOWN, PLAY, PAUSE\r\n"
            f"\r\n"
        )
        
    def _create_describe_response(self, cseq):
        """Crée une réponse DESCRIBE avec SDP pour streaming vidéo."""
        sdp_content = (
            f"v=0\r\n"
            f"o=- 123456 654321 IN IP4 localhost\r\n"
            f"s={self.user.name} Camera Stream\r\n"
            f"t=0 0\r\n"
            f"m=video 0 RTP/AVP 96\r\n"
            f"a=rtpmap:96 JPEG/90000\r\n"
            f"a=control:track1\r\n"
            f"a=framerate:30\r\n"
        )
        
        return (
            f"RTSP/1.0 200 OK\r\n"
            f"CSeq: {cseq}\r\n"
            f"Content-Type: application/sdp\r\n"
            f"Content-Length: {len(sdp_content)}\r\n"
            f"\r\n"
            f"{sdp_content}"
        )
        
    def _create_setup_response(self, cseq, headers, stream: RTSPVideoStream):
        """Crée une réponse SETUP avec configuration transport."""
        transport_header = headers.get('transport', '')
        client_ports = None
        
        # Extraire les ports client depuis l'en-tête Transport
        if 'client_port=' in transport_header:
            parts = transport_header.split('client_port=')[1].split(';')[0]
            client_ports = parts
            
        # Configurer le transport
        transport_info = stream.setup_transport(client_ports) if client_ports else None
        
        if transport_info:
            transport_response = (f"RTP/AVP;unicast;client_port={transport_info['client_ports']};"
                                f"server_port={transport_info['server_ports']}")
        else:
            transport_response = "RTP/AVP;unicast;client_port=8000-8001;server_port=8002-8003"
            
        return (
            f"RTSP/1.0 200 OK\r\n"
            f"CSeq: {cseq}\r\n"
            f"Session: {stream.session_id}\r\n"
            f"Transport: {transport_response}\r\n"
            f"\r\n"
        )
        
    def _create_play_response(self, cseq, session_id):
        """Crée une réponse PLAY."""
        return (
            f"RTSP/1.0 200 OK\r\n"
            f"CSeq: {cseq}\r\n"
            f"Range: npt=0.000-\r\n"
            f"Session: {session_id}\r\n"
            f"RTP-Info: url=rtsp://localhost:{self.user.rtsp_port}/stream/track1\r\n"
            f"\r\n"
        )
        
    def _create_teardown_response(self, cseq):
        """Crée une réponse TEARDOWN."""
        return (
            f"RTSP/1.0 200 OK\r\n"
            f"CSeq: {cseq}\r\n"
            f"\r\n"
        )
        
    def _create_error_response(self, cseq, error):
        """Crée une réponse d'erreur."""
        return (
            f"RTSP/1.0 {error}\r\n"
            f"CSeq: {cseq}\r\n"
            f"\r\n"
        )