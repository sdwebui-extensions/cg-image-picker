from server import PromptServer
from aiohttp import web
import time
from comfy.cli_args import args
import requests
import folder_paths

class Cancelled(Exception):
    pass

class MessageHolder:
    stash = {}
    messages = {}
    cancelled = False
    
    @classmethod
    def addMessage(cls, id, message):
        if message=='__cancel__':
            cls.messages = {}
            cls.cancelled = True
        elif message=='__start__':
            cls.messages = {}
            cls.stash = {}
            cls.cancelled = False
        else:
            cls.messages[str(id)] = message
    
    @classmethod
    def waitForMessage(cls, id, period = 0.1, asList = False):
        sid = str(id)
        while not (sid in cls.messages) and not ("-1" in cls.messages):
            if cls.cancelled:
                cls.cancelled = False
                raise Cancelled()
            time.sleep(period)
        if cls.cancelled:
            cls.cancelled = False
            raise Cancelled()
        message = cls.messages.pop(str(id),None) or cls.messages.pop("-1")
        try:
            if asList:
                return [int(x.strip()) for x in message.split(",")]
            else:
                return int(message.strip())
        except ValueError:
            print(f"ERROR IN IMAGE_CHOOSER - failed to parse '${message}' as ${'comma separated list of ints' if asList else 'int'}")
            return [1] if asList else 1

routes = PromptServer.instance.routes
@routes.post('/image_chooser_message')
async def make_image_selection(request):
    if folder_paths.prompt_host is not None:
        return web.json_response({})
    post = await request.post()
    MessageHolder.addMessage(post.get("id"), post.get("message"))
    if args.just_ui:
        requests.get(f'http://{folder_paths.server_host}/image_chooser_message', headers={"Authorization": folder_paths.token}, timeout=1, json={"id":post.get("id"), "message":post.get("message")})
    return web.json_response({})

@routes.get('/image_chooser_message')
async def make_image_selection(request):
    post = await request.json()
    MessageHolder.addMessage(post.get("id"), post.get("message"))
    return web.json_response({})