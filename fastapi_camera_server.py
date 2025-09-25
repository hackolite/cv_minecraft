#!/usr/bin/env python3
"""
FastAPI Camera Server for Observer Cameras
Serveur FastAPI pour caméras d'observateurs

Ce module remplace le système RTSP par une interface web FastAPI
pour visualiser ce que voient les caméras d'observateurs.
"""

import asyncio
import logging
import time
import io
import base64
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from observer_camera import ObserverCamera, camera_manager


class CameraInfo(BaseModel):
    """Information about a camera."""
    observer_id: str
    position: tuple
    rotation: tuple
    resolution: tuple
    is_capturing: bool


class FastAPICameraServer:
    """Serveur FastAPI pour le streaming des caméras d'observateurs."""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="Observer Camera Server",
            description="Interface web pour visualiser les caméras d'observateurs Minecraft"
        )
        self.active_cameras: Dict[str, ObserverCamera] = {}
        self.websocket_connections: List[WebSocket] = []
        self.logger = logging.getLogger(__name__)
        self.setup_routes()
        
    def setup_routes(self):
        """Configure les routes FastAPI."""
        
        @self.app.get("/")
        async def home():
            """Page d'accueil avec interface web."""
            return HTMLResponse(content=self.get_web_interface())
        
        @self.app.get("/cameras", response_model=List[CameraInfo])
        async def list_cameras():
            """Liste toutes les caméras disponibles."""
            cameras_info = []
            for camera in camera_manager.get_all_cameras():
                cameras_info.append(CameraInfo(
                    observer_id=camera.observer_id,
                    position=camera.position,
                    rotation=camera.rotation,
                    resolution=camera.resolution,
                    is_capturing=camera.is_capturing
                ))
            return cameras_info
        
        @self.app.get("/camera/{observer_id}/image")
        async def get_camera_image(observer_id: str):
            """Récupère la dernière image d'une caméra."""
            camera = camera_manager.get_camera(observer_id)
            if not camera:
                raise HTTPException(status_code=404, detail=f"Camera {observer_id} not found")
            
            frame = camera.get_latest_frame()
            if not frame:
                raise HTTPException(status_code=404, detail=f"No frame available for camera {observer_id}")
            
            return StreamingResponse(
                io.BytesIO(frame['data']),
                media_type="image/jpeg",
                headers={"Cache-Control": "no-cache"}
            )
        
        @self.app.get("/camera/{observer_id}/stream")
        async def get_camera_stream(observer_id: str):
            """Stream MJPEG pour une caméra."""
            camera = camera_manager.get_camera(observer_id)
            if not camera:
                raise HTTPException(status_code=404, detail=f"Camera {observer_id} not found")
            
            def generate():
                while True:
                    frame = camera.get_latest_frame()
                    if frame:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame['data'] + b'\r\n')
                    time.sleep(0.1)  # 10 FPS
            
            return StreamingResponse(
                generate(),
                media_type="multipart/x-mixed-replace; boundary=frame"
            )
        
        @self.app.websocket("/ws/camera/{observer_id}")
        async def websocket_camera_stream(websocket: WebSocket, observer_id: str):
            """WebSocket pour streaming temps réel d'une caméra."""
            camera = camera_manager.get_camera(observer_id)
            if not camera:
                await websocket.close(code=4004)
                return
            
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            try:
                while True:
                    frame = camera.get_latest_frame()
                    if frame:
                        # Encoder l'image en base64 pour WebSocket
                        frame_b64 = base64.b64encode(frame['data']).decode('utf-8')
                        await websocket.send_json({
                            "type": "frame",
                            "observer_id": observer_id,
                            "timestamp": frame['timestamp'],
                            "position": frame['position'],
                            "rotation": frame['rotation'],
                            "data": frame_b64
                        })
                    await asyncio.sleep(0.1)  # 10 FPS
                    
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
        
        @self.app.post("/camera/{observer_id}/move")
        async def move_camera(observer_id: str, position: List[float], rotation: List[float] = None):
            """Déplace une caméra à une nouvelle position."""
            camera = camera_manager.get_camera(observer_id)
            if not camera:
                raise HTTPException(status_code=404, detail=f"Camera {observer_id} not found")
            
            if len(position) != 3:
                raise HTTPException(status_code=400, detail="Position must have 3 coordinates [x, y, z]")
            
            rotation_tuple = None
            if rotation:
                if len(rotation) != 2:
                    raise HTTPException(status_code=400, detail="Rotation must have 2 coordinates [yaw, pitch]")
                rotation_tuple = tuple(rotation)
            
            camera.update_position(tuple(position), rotation_tuple)
            return {"message": f"Camera {observer_id} moved to {position}"}
    
    def get_web_interface(self) -> str:
        """Génère l'interface web HTML."""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Observer Camera Server</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f0f0f0; }
        .header { background-color: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .cameras-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }
        .camera-card { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .camera-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #2c3e50; }
        .camera-info { margin-bottom: 15px; font-size: 14px; color: #666; }
        .camera-stream { width: 100%; height: 300px; border: 2px solid #ddd; border-radius: 4px; background: #000; }
        .camera-controls { margin-top: 10px; }
        .btn { padding: 8px 16px; margin: 4px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-primary { background-color: #3498db; color: white; }
        .btn-secondary { background-color: #95a5a6; color: white; }
        .no-cameras { text-align: center; padding: 40px; color: #666; }
        .status { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        .status-active { background-color: #2ecc71; color: white; }
        .status-inactive { background-color: #e74c3c; color: white; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎥 Observer Camera Server</h1>
        <p>Interface web pour visualiser les caméras d'observateurs Minecraft</p>
    </div>
    
    <div id="cameras-container">
        <div class="no-cameras">Chargement des caméras...</div>
    </div>

    <script>
        let cameras = [];
        
        async function loadCameras() {
            try {
                const response = await fetch('/cameras');
                cameras = await response.json();
                renderCameras();
            } catch (error) {
                console.error('Erreur chargement caméras:', error);
                document.getElementById('cameras-container').innerHTML = 
                    '<div class="no-cameras">Erreur de chargement des caméras</div>';
            }
        }
        
        function renderCameras() {
            const container = document.getElementById('cameras-container');
            
            if (cameras.length === 0) {
                container.innerHTML = '<div class="no-cameras">Aucune caméra disponible</div>';
                return;
            }
            
            const grid = document.createElement('div');
            grid.className = 'cameras-grid';
            
            cameras.forEach(camera => {
                const card = document.createElement('div');
                card.className = 'camera-card';
                
                const statusClass = camera.is_capturing ? 'status-active' : 'status-inactive';
                const statusText = camera.is_capturing ? 'ACTIF' : 'INACTIF';
                
                card.innerHTML = `
                    <div class="camera-title">
                        📹 ${camera.observer_id}
                        <span class="status ${statusClass}">${statusText}</span>
                    </div>
                    <div class="camera-info">
                        <strong>Position:</strong> (${camera.position.join(', ')})<br>
                        <strong>Rotation:</strong> (${camera.rotation.join(', ')})<br>
                        <strong>Résolution:</strong> ${camera.resolution.join('x')}
                    </div>
                    <img class="camera-stream" 
                         src="/camera/${camera.observer_id}/stream" 
                         alt="Stream ${camera.observer_id}"
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                    <div style="display:none; text-align:center; padding:40px; color:#999;">
                        Stream non disponible
                    </div>
                    <div class="camera-controls">
                        <button class="btn btn-primary" onclick="refreshCamera('${camera.observer_id}')">
                            🔄 Actualiser
                        </button>
                        <button class="btn btn-secondary" onclick="openSingleView('${camera.observer_id}')">
                            🔍 Vue détaillée
                        </button>
                    </div>
                `;
                
                grid.appendChild(card);
            });
            
            container.innerHTML = '';
            container.appendChild(grid);
        }
        
        function refreshCamera(observerId) {
            const img = document.querySelector(`img[src*="${observerId}"]`);
            if (img) {
                img.src = img.src.split('?')[0] + '?t=' + Date.now();
            }
        }
        
        function openSingleView(observerId) {
            window.open(`/camera/${observerId}/stream`, '_blank');
        }
        
        // Chargement initial et actualisation périodique
        loadCameras();
        setInterval(loadCameras, 10000); // Actualiser toutes les 10 secondes
    </script>
</body>
</html>
        """
    
    async def start_server(self):
        """Démarre le serveur FastAPI."""
        import uvicorn
        self.logger.info(f"Starting FastAPI Camera Server on http://{self.host}:{self.port}")
        
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    def set_world_model(self, world_model):
        """Définit le modèle du monde pour les caméras."""
        camera_manager.set_world_model(world_model)
    
    def get_server_info(self) -> Dict[str, str]:
        """Retourne les informations du serveur."""
        return {
            "url": f"http://{self.host}:{self.port}",
            "cameras_api": f"http://{self.host}:{self.port}/cameras",
            "web_interface": f"http://{self.host}:{self.port}/"
        }


# Instance globale du serveur FastAPI
fastapi_camera_server = FastAPICameraServer()


async def main():
    """Démonstration du serveur FastAPI."""
    # Créer quelques caméras de test
    camera_manager.create_camera("test_camera_1", (30, 50, 80), (0, 0))
    camera_manager.create_camera("test_camera_2", (50, 50, 60), (90, 0))
    camera_manager.create_camera("test_camera_3", (70, 50, 40), (180, 0))
    
    # Démarrer les caméras individuellement
    for camera in camera_manager.get_all_cameras():
        camera.start_capture(None)
    
    # Démarrer le serveur
    await fastapi_camera_server.start_server()


if __name__ == "__main__":
    asyncio.run(main())