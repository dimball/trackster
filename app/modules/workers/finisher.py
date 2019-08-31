from __future__ import print_function
from __future__ import unicode_literals
import threading
import shutil
import os
from common.utility import Utility
class Worker(threading.Thread, Utility):
    def __init__(self, main, params):
        threading.Thread.__init__(self)
        self.params = params
        self.setName("finish worker")
        self.isRunning = True
        self.finishQueue = main.finishQueue
        self.plexQueue = main.plexQueue
        self.dataTransport = main.dataTransport
        self.main = main

    def stop(self):
        # poison pill
        self.isRunning = False
        self.add('STOP')
    def add(self,payload):
        # self.printMessage("adding:%s" % payload)
        self.finishQueue.put(payload)
    def run(self):
        self.printMessage("Thread is running:%s" % self.getName())
        while self.isRunning:
            try:
                payload = self.finishQueue.get()
                if payload is 'STOP':
                    break
                if not self.isRunning:
                    break


                artist = payload['title']['playlist']['artist']
                if artist == '-1' or artist == '':
                    artist = "Various Artists"


                album = payload['title']['playlist']['album']
                if album == '-1' or album == '':
                    album = 'Mix'

                targetfolder = self.params['folder']['complete'] + "/" + artist + "/" + artist + " - " + album
                sourcefolder = self.params['folder']['incomplete'] + "/" + artist + "/" + artist + " - " + album

                if not os.path.exists(targetfolder):
                    os.makedirs(targetfolder)
                if os.path.exists(sourcefolder):
                    for file in os.listdir(sourcefolder):
                        filename, ext = os.path.split(file)
                        shutil.move(sourcefolder + "/" + file, targetfolder + "/" + filename + ext)
                        self.printMessage("Moving file: " + sourcefolder + "/" + file +  " ---> " + targetfolder + "/" + filename + ext)

                    if len(os.listdir(sourcefolder + "/")) == 0:
                        self.printMessage("Removing folder:" + targetfolder)
                        os.rmdir(sourcefolder + "/")
                        parentfolder = os.path.dirname(sourcefolder)
                        if len(os.listdir(parentfolder + "/")) == 1:
                            if os.listdir(parentfolder + "/")[0] == '.DS_Store':
                                os.remove(parentfolder + "/" + os.listdir(parentfolder + "/")[0])

                        if len(os.listdir(parentfolder + "/")) == 0:
                            os.rmdir(parentfolder + "/")
                            self.printMessage("Removing folder:" + parentfolder)

                    self.plexQueue.put("finished")
                else:
                    self.printMessage("Source folder:{} does not exist".format(sourcefolder))


                self.finishQueue.task_done()
            except KeyboardInterrupt:
                break
        self.printMessage("Thread is exiting:%s" % self.getName())
