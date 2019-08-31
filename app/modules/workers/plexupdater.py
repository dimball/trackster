from __future__ import print_function
from __future__ import unicode_literals
import requests
import threading
import time
import xml.etree.ElementTree as etree
from common.utility import Utility

class Worker(threading.Thread, Utility):
    def __init__(self, main, params):
        threading.Thread.__init__(self)
        self.params = params
        self.setName("plex updater")
        self.isRunning = True
        self.plexQueue = main.plexQueue
        self.dataTransport = main.dataTransport
        self.main = main
    def stop(self):
        # poison pill
        self.isRunning = False
        self.add('STOP')
    def add(self,payload):
        # self.printMessage("adding:%s" % payload)
        self.plexQueue.put(payload)


    def run(self):
        self.printMessage("Thread is running:%s" % self.getName())
        while self.isRunning:
            try:
                payload = self.plexQueue.get()
                if payload is 'STOP':
                    break
                if not self.isRunning:
                    break
                timerCounter = 0

                self.params['plexrun'] = True
                while self.params['plexrun'] == True:

                    if timerCounter == self.params['plexTimer']:
                        if self.params['folder']['mode'] == 'production':
                            self.printMessage("Updating plex server at:" + self.params['plexURL'])
                            response = requests.get('http://' + self.params['plexURL'] + '/library/sections?X-Plex-Token=' + self.params['plexToken'])
                            tree = etree.fromstring(response.content)
                            for child in tree:
                                if child.attrib['type'] == 'artist':
                                    request.urlopen('http://' + self.params['plexURL'] + '/library/sections/' + child.attrib['key'] + '/refresh?X-Plex-Token=' + self.params['plexToken'])
                        else:
                            self.printMessage("Dev mode: Not refreshing plex library")
                        break
                    self.printMessage("Countdown until plex refresh:" + str(self.params['plexTimer']-timerCounter))
                    time.sleep(1)
                    timerCounter += 1

                self.plexQueue.task_done()
                if not self.params['plexrun']:
                    self.printMessage("Plex timer was aborted")
            except KeyboardInterrupt:
                break
        self.printMessage("Thread is exiting:%s" % self.getName())
