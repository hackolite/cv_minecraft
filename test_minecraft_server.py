import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")

SERVER_URI = "ws://localhost:8765"


async def recv_json(ws):
    msg = await ws.recv()
    logging.info(f"Reçu <- {msg}")
    return json.loads(msg)


async def send_json(ws, msg_type, data=None):
    msg = {"type": msg_type}
    if data:
        msg["data"] = data
    await ws.send(json.dumps(msg))
    logging.info(f"Envoyé -> {msg}")


async def test_connection():
    async with websockets.connect(SERVER_URI) as ws:
        await send_json(ws, "player_join", {"name": "Tester"})
        init_msg = await recv_json(ws)
        assert init_msg["type"] == "world_init"
        logging.info("✅ Test connexion utilisateur réussi")


async def test_block_create_destroy():
    async with websockets.connect(SERVER_URI) as ws:
        # Send player join
        join_msg = {"type": "player_join", "data": {"name": "Builder"}}
        await ws.send(json.dumps(join_msg))
        logging.info(f"Envoyé -> {join_msg}")
        
        # Receive world_init
        resp_raw = await ws.recv()
        resp = json.loads(resp_raw)
        logging.info(f"Reçu <- {resp_raw}")
        assert resp["type"] == "world_init"
        logging.info("✅ Test de renvoie de chunk reussi")
        
        # Wait for all chunk messages and player_list to complete
        chunks_received = 0
        while True:
            msg_raw = await ws.recv()
            data = json.loads(msg_raw)
            logging.info(f"Reçu <- {msg_raw}")
            if data["type"] == "world_chunk":
                chunks_received += 1
            elif data["type"] == "player_list":
                logging.info(f"Received player_list after {chunks_received} chunks - initialization complete")
                break
            else:
                logging.info(f"Unexpected message during init: {data['type']}")
                break
        
        # Place block at a unique position to avoid conflicts
        import random
        x, z = random.randint(10, 100), random.randint(10, 100)
        test_position = [x, 90, z]  # Use Y=90 to be well above terrain
        
        block_msg = {"type": "block_place", "data": {"position": test_position, "block_type": "stone"}}
        await ws.send(json.dumps(block_msg))
        logging.info(f"Envoyé -> {block_msg}")
        
        # Receive response
        resp_raw = await ws.recv()
        resp = json.loads(resp_raw)
        logging.info(f"Reçu <- {resp_raw}")

        logging.info(f"Expected world_update, got: {resp['type']}")
        logging.info(f"Full response: {resp}")
        assert resp["type"] == "world_update", f"Expected world_update but got {resp['type']}: {resp}"
        logging.info("✅ Test création de bloc réussi")

        # Destroy block
        destroy_msg = {"type": "block_destroy", "data": {"position": test_position}}
        await ws.send(json.dumps(destroy_msg))
        logging.info(f"Envoyé -> {destroy_msg}")
        
        # Receive destroy response
        resp_raw = await ws.recv()
        resp = json.loads(resp_raw)
        logging.info(f"Reçu <- {resp_raw}")
        logging.info("✅ Test destruction de bloc réussi")


async def test_player_relative_move():
    async with websockets.connect(SERVER_URI) as ws:
        # Send player join
        join_msg = {"type": "player_join", "data": {"name": "Mover"}}
        await ws.send(json.dumps(join_msg))
        logging.info(f"Envoyé -> {join_msg}")
        
        # Receive world_init
        resp_raw = await ws.recv()
        init_msg = json.loads(resp_raw)
        logging.info(f"Reçu <- {resp_raw}")

        # Nouvelle position initiale
        position = init_msg.get("spawn_position", [30, 50, 80])
        logging.info(f"Position initiale : {position}")

        # Wait for all chunk messages and player_list to complete
        chunks_received = 0
        while True:
            msg_raw = await ws.recv()
            data = json.loads(msg_raw)
            logging.info(f"Reçu <- {msg_raw}")
            if data["type"] == "world_chunk":
                chunks_received += 1
            elif data["type"] == "player_list":
                logging.info(f"Received player_list after {chunks_received} chunks - initialization complete")
                break
            else:
                logging.info(f"Unexpected message during init: {data['type']}")
                break

        # Déplacement relatif
        delta = [5, 2, 1]  # déplacement dx, dy, dz
        move_msg = {"type": "player_move", "data": {"delta": delta, "rotation": [0, 90]}}
        await ws.send(json.dumps(move_msg))
        logging.info(f"Envoyé -> {move_msg}")

        # Receive response
        resp_raw = await ws.recv()
        resp = json.loads(resp_raw)
        logging.info(f"Reçu <- {resp_raw}")
        
        assert resp["type"] == "player_update"
        new_pos = resp["data"]["position"]
        expected_pos = [position[0]+delta[0], position[1]+delta[1], position[2]+delta[2]]
        assert new_pos == expected_pos, f"Position attendue {expected_pos}, obtenue {new_pos}"
        logging.info(f"✅ Test déplacement relatif réussi : {new_pos}")


async def main():
    #await test_connection()
    await test_block_create_destroy()
    await test_player_relative_move()
    logging.info("🎉 Tous les tests sont passés avec succès !")


if __name__ == "__main__":
    asyncio.run(main())
