import argparse
import logging
import asyncio
import hashlib
from datetime import datetime
from aiohttp import web

from kademlia.network import Server

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log = logging.getLogger('kademlia')
log.addHandler(handler)
log.setLevel(logging.DEBUG)

server = None


def parse_arguments():
    parser = argparse.ArgumentParser()

    # Optional arguments
    parser.add_argument("-i", "--ip", help="IP address of existing node", type=str, default=None)
    parser.add_argument("-p", "--port", help="port number of existing node", type=int, default=None)
    parser.add_argument("-l", "--listen", help="listen port of this node,default=17168", type=int, default=17168)
    parser.add_argument("-k", "--ksize", help="ksize of this kad network", type=int, default=20)

    return parser.parse_args()

def generate_token():
    current_utc_time = datetime.utcnow()
    seed_value = current_utc_time.strftime('%Y?%m?%d?%H?%M?').encode('utf-8')
    hash_obj = hashlib.sha256(seed_value)
    return hash_obj.hexdigest()[:24]

async def set_key_value(request):
    """
    Handle setting a key-value pair via HTTP using GET request.
    """
    token = request.rel_url.query.get('token')
    key = request.rel_url.query.get('key')
    value = request.rel_url.query.get('value')
    
    if not token or not key or not value:
        return web.Response(text="'token' and 'key' and 'value' parameters are required.", status=400)

    if token!=generate_key():
        return web.Response(text="Invalid token,request failed", status=500)
        
    await server.set(key, value)
    return web.Response(text="Key-Value set successfully")

async def set_key_value_POST(request):
    """
    Handle setting a key-value pair via HTTP, Do not need token.
    """
    data = await request.json()
    key = data.get('key')
    value = data.get('value')
    if not key or not value:
        return web.Response(text="Key and value required", status=400)
    await server.set(key, value)
    return web.Response(text="Key-Value set successfully")

async def get_neighbors(request):
    """
    Handle retrieving all neighbors
    """
    token = request.rel_url.query.get('token')
    if not token or not key:
        return web.Response(text="A 'token' parameter is required.", status=400)
        
    if token!=generate_key():
        return web.Response(text="Invalid token,request failed", status=500)
        
    try:
        value = server.bootstrappable_neighbors()
        return web.Response(text=str([t[0] for t in value]))
    except Exception as e:
        return web.Response(text=str(e), status=500)

async def get_key_value(request):
    """
    Handle retrieving a value from HTTP based on a key.
    """
    token = request.rel_url.query.get('token')
    key = request.rel_url.query.get('key')
    if not token or not key:
        return web.Response(text="A 'token' and 'key' parameter is required.", status=400)
        
    if token!=generate_key():
        return web.Response(text="Invalid token,request failed", status=500)
    try:
        value = await server.get(key)
        return web.Response(text=value)
    except Exception as e:
        return web.Response(text=str(e), status=500)

async def start_http_server():
    app = web.Application()
    app.add_routes([web.get('/set', set_key_value)])
    app.add_routes([web.get('/get', get_key_value)])
    app.add_routes([web.get('/neighbors', get_neighbors)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8083)
    await site.start()

def connect_to_bootstrap_node(args):
    global server
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    server = Server(ksize=args.ksize)
    loop.run_until_complete(server.listen(int(args.listen)))
    bootstrap_node = (args.ip, int(args.port))
    loop.run_until_complete(server.bootstrap([bootstrap_node]))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
        loop.close()


def create_bootstrap_node(args):
    global server
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    server = Server(ksize=args.ksize)
    loop.run_until_complete(server.listen(int(args.listen)))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
        loop.close()


def main():
    args = parse_arguments()
# Start the HTTP server
    loop = asyncio.get_event_loop()
    loop.create_task(start_http_server())

    if args.ip and args.port:
        connect_to_bootstrap_node(args)
    else:
        create_bootstrap_node(args)


if __name__ == "__main__":
    main()
