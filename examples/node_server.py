import argparse
import logging
import asyncio
from aiohttp import web

from kademlia.network import Server

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log = logging.getLogger('kademlia')
log.addHandler(handler)
log.setLevel(logging.DEBUG)

server = Server()


def parse_arguments():
    parser = argparse.ArgumentParser()

    # Optional arguments
    parser.add_argument("-i", "--ip", help="IP address of existing node", type=str, default=None)
    parser.add_argument("-p", "--port", help="port number of existing node", type=int, default=None)
    parser.add_argument("-l", "--listen", help="listen port of this node,default=17168(first node)/17169(second node)", type=int, default=17168)

    return parser.parse_args()


async def set_key_value(request):
    """
    Handle setting a key-value pair via HTTP using GET request.
    """
    key = request.rel_url.query.get('key')
    value = request.rel_url.query.get('value')
    
    if not key or not value:
        return web.Response(text="Both 'key' and 'value' parameters are required.", status=400)
    
    await server.set(key, value)
    return web.Response(text="Key-Value set successfully")

async def set_key_value_POST(request):
    """
    Handle setting a key-value pair via HTTP
    """
    data = await request.json()
    key = data.get('key')
    value = data.get('value')
    if not key or not value:
        return web.Response(text="Key and value required", status=400)
    await server.set(key, value)
    return web.Response(text="Key-Value set successfully")

async def get_key_value(request):
    """
    Handle retrieving a value from HTTP based on a key.
    """
    key = request.rel_url.query.get('key')
    if not key:
        return web.Response(text="A 'key' parameter is required.", status=400)
    try:
        value = await server.get(key)
        return web.Response(text=value)
    except Exception as e:
        return web.Response(text=str(e), status=500)

async def start_http_server():
    app = web.Application()
    app.add_routes([web.get('/set', set_key_value)])
    app.add_routes([web.get('/get', get_key_value)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', 8083)
    await site.start()

def connect_to_bootstrap_node(args):
    loop = asyncio.get_event_loop()
    loop.set_debug(True)

    loop.run_until_complete(server.listen(int(args.listen)+1))
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
    loop = asyncio.get_event_loop()
    loop.set_debug(True)

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
