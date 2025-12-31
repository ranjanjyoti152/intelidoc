"""
InteliDoc RAG Pipeline - WebSocket Routes
Real-time document processing status updates via WebSocket.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: Dict):
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return
        
        message_json = json.dumps(message)
        disconnected = set()
        
        async with self._lock:
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_json)
                except Exception as e:
                    logger.warning(f"Failed to send message to client: {e}")
                    disconnected.add(connection)
            
            # Remove disconnected clients
            self.active_connections -= disconnected


# Global connection manager singleton
manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    return manager


@router.websocket("/ws/documents")
async def websocket_documents(websocket: WebSocket):
    """WebSocket endpoint for real-time document status updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, handle incoming messages if needed
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                # Handle ping/pong or other messages
                if data == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except asyncio.TimeoutError:
                # Send keepalive
                try:
                    await websocket.send_text(json.dumps({"type": "keepalive"}))
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await manager.disconnect(websocket)


async def broadcast_document_status(
    document_id: int,
    status: str,
    filename: str,
    progress: int = 0,
    message: str = "",
    chunk_count: int = 0,
    error: str = ""
):
    """
    Broadcast a document status update to all connected clients.
    
    Args:
        document_id: The document ID
        status: Current status (pending, processing, completed, failed)
        filename: Original filename
        progress: Processing progress percentage (0-100)
        message: Optional status message
        chunk_count: Number of chunks processed (for completed status)
        error: Error message (for failed status)
    """
    await manager.broadcast({
        "type": "document_status",
        "document_id": document_id,
        "status": status,
        "filename": filename,
        "progress": progress,
        "message": message,
        "chunk_count": chunk_count,
        "error": error,
    })
