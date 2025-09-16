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
        await send_json(ws, "player_join", {"name": "Builder"})
        resp = await recv_json(ws)  # WORLD_INIT
        assert resp["type"] == "world_init"
        logging.info("✅ Test de renvoie de chunk reussi")
        # Place block
        await send_json(ws, "block_place", {
            "position": [40, 50, 40],
            "block_type": "stone"
        })
        resp = await recv_json(ws)

        assert resp["type"] == "world_update"
        logging.info("✅ Test création de bloc réussi")

        # Destroy block
        await send_json(ws, "block_destroy", {
            "position": [40, 50, 40]
        })
        resp = await recv_json(ws)
        logging.info("✅ Test destruction de bloc réussi")


async def test_player_relative_move():
    async with websockets.connect(SERVER_URI) as ws:
        await send_json(ws, "player_join", {"name": "Mover"})
        init_msg = await recv_json(ws)  # WORLD_INIT

        # Nouvelle position initiale
        position = init_msg.get("spawn_position", [30, 50, 80])
        logging.info(f"Position initiale : {position}")

        # Déplacement relatif
        delta = [5, 2, 1]  # déplacement dx, dy, dz
        await send_json(ws, "player_move", {
            "delta": delta,
            "rotation": [0, 90]
        })

        resp = await recv_json(ws)
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
