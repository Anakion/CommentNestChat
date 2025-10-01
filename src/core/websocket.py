from typing import List, Dict, Any
from fastapi import WebSocket
import json


class ConnectionManager:
    def __init__(self):
        # Список активных соединений
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, comments: list):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Новое подключение. Всего подключений: {len(self.active_connections)}")
        await self.send_comments(websocket, comments)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_comments(self, websocket: WebSocket, comments: list):
        """Отправка всех комментариев одному клиенту"""
        data = json.dumps({"type": "all_comments", "data": comments}, default=str)
        try:
            await websocket.send_text(data)
        except Exception:
            self.disconnect(websocket)

    async def broadcast_comments(self, comments: list):
        """Рассылает всем клиентам список комментариев"""
        data = json.dumps({"type": "all_comments", "data": comments}, default=str)
        to_remove = []
        for ws in self.active_connections:
            try:
                await ws.send_text(data)
            except Exception:
                to_remove.append(ws)
        for ws in to_remove:
            self.disconnect(ws)

    async def broadcast_new_comment(self, comment: dict):
        """Рассылает только новый комментарий"""
        # comment уже dict с полями комментария
        data = json.dumps({"type": "new_comment", "data": comment}, default=str)
        to_remove = []
        for ws in self.active_connections:
            try:
                await ws.send_text(data)
            except Exception:
                to_remove.append(ws)
        for ws in to_remove:
            self.disconnect(ws)

    # async def broadcast_new_comment(self, comment: dict):
    #     """Рассылает только новый комментарий"""
    #     data = json.dumps({"type": "new_comment", "data": comment}, default=str)
    #     to_remove = []
    #     for ws in self.active_connections:
    #         try:
    #             await ws.send_text(data)
    #         except Exception as e:
    #             to_remove.append(ws)
    #     for ws in to_remove:
    #         self.disconnect(ws)


# Глобальный экземпляр
manager = ConnectionManager()
