import tornado.web
import tornado.websocket
import tornado.httpserver
import tornado.ioloop
from tornado import gen
from tornado import queues
import os
import json
import YtDownloader_multithreaded
from multiprocessing import JoinableQueue
from queue import Queue
import uuid
# public_root = os.path.join(os.path.dirname(__file__), 'public')
class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def initialize(self, data):
        self.data = data
    connections = []
    def createDataItem(self, type, payload):
        data = {
            'type': type,
            'payload': payload
        }
        return data
    def open(self):

        self.data['connections'].append(self)
        newUUID =  uuid.uuid4()
        self.data['connection_id'][str(newUUID)] = self
        print("Adding client:" + str(newUUID) + " to pool")
    #     send back the new uuid to the connected client
        self.write_message(self.createDataItem('client/set/clientid', str(newUUID)))

    def on_message(self, data):
        for connection in self.data['connections']:
            connection.write_message(data)

        payload = json.loads(data)

        # if payload['type'] == 'server/add/url':
        #     self.data['playlist'].put(payload['payload'])
        if payload['type'] == 'server/login':
            if payload['payload']['password'] == '1234':
                self.render("index.html", data=self.data)
        else:
            self.data['data_transport'].put(payload)

    def on_close(self):
        targetId = None
        for connection in self.data['connections']:
            if connection == self:
                for id in self.data['connection_id']:
                    if self.data['connection_id'][id] == connection:
                        targetId = id
                        print("Removing ID:" + id)

        if targetId != None:
            del self.data['connection_id'][targetId]

        self.data['connections'].remove(self)

class IndexPageHandler(tornado.web.RequestHandler):
    def initialize(self, data):
        self.data = data['structure']
    def get(self):
        data = ""
        # self.render("login.html", data=data)
        self.render("index.html", data=data)


class Application(tornado.web.Application):
    def __init__(self):


        self.ConvertQueueResult = JoinableQueue()
        self.PlaylistQueue = Queue()
        self.MessageQueue = queues.Queue()
        self.dataTransport = JoinableQueue()
        self.data = {}
        self.data['MessageQueue'] = self.MessageQueue
        self.data['convert_result'] = self.ConvertQueueResult
        self.data['data_transport'] = self.dataTransport
        self.data['playlist'] = self.PlaylistQueue
        self.data['structure'] = {
            'items': [],
            'index':{}
        }





        self.data['connections'] = []
        self.data['connection_id'] = {}

        handlers = [
            (r'/', IndexPageHandler, dict(data=self.data)),
            # (r'/(.*)', tornado.web.StaticFileHandler, {'path': public_root}),
            (r'/websocket', WebSocketHandler, dict(data=self.data))
        ]
        templatePath = 'templates'
        if not os.path.exists("./templates"):
            templatePath = 'app/templates'
            print("using Production mode. path:" + templatePath)
        else:
            print("using Dev mode path:" + templatePath)

        settings = {
            'template_path': templatePath,
            'static_path' : os.path.join(os.path.dirname(__file__), "static")
        }
        # print(settings)
        self.Ytdownloader = YtDownloader_multithreaded.Main(self.data)
        self.Ytdownloader.start()

        tornado.web.Application.__init__(self, handlers, **settings)

    @gen.coroutine
    def consumer(self):
        while True:
            data = yield self.MessageQueue.get()
            try:
                # print('Doing work on %s' % data['payload'])
                options = data['type']
                payload = data['payload']

                if options['targetClientID'] == None:
                    for client in self.data['connections']:
                        client.write_message(payload)
                else:
                    if not options['bInvert']:
                        self.data['connection_id'][options['targetClientID']].write_message(payload)
                    else:
                        for client in self.data['connection_id']:
                            if client != options['targetClientID']:
                                self.data['connection_id'][client].write_message(payload)

                yield
                    # gen.sleep(0.001)
            finally:
                self.MessageQueue.task_done()


if __name__ == '__main__':

    ws_app = Application()
    server = tornado.httpserver.HTTPServer(ws_app)
    server.listen(8080)
    try:
        tornado.ioloop.IOLoop.current().spawn_callback(ws_app.consumer)
        tornado.ioloop.IOLoop.instance().start()
        # yield ws_app.MessageQueue.join()
    except KeyboardInterrupt:
        ws_app.Ytdownloader.stop()