from __future__ import print_function
from __future__ import unicode_literals
import youtube_dl
import threading
import time
import random
from common.utility import Utility
class Worker(threading.Thread, Utility):
    def __init__(self, main, id):
        # Process.__init__(self)
        threading.Thread.__init__(self)
        self.downloadQueue = main.DownloadQueue
        self.convertQueue = main.ConvertQueue
        # self.setName("Download Worker")
        self.name = "Download worker " + str(id)
        self.isRunning = True
        self.main = main
        self.playListData = {}
        self.playlistItem = None
    def _download_hook(self, d):
        if d['status'] == 'finished':

            # the file has been downloaded, needs to check if this is for a split album or not

            if self.playlistItem['playlist']['type'] == 'splitalbum':
                for videoItem in self.playlistItem['items']:
                    entryData = {
                        'filename': d['filename'],
                        'playlistData': self.playListData,
                        'playlistItem': self.playlistItem,
                        'videoItem': videoItem
                    }

                    # self.sendProgressMessage(self.main.dataTransport, filedata, "waiting to convert")
                    self.addConvertItem(entryData)

            else:
                # self.printMessage(d)
                entryData = {
                    'filename': d['filename'],
                    'playlistData': self.playListData,
                    'playlistItem': self.playlistItem

                }
                filedata = self.GetDataFromFilename(d['filename'])
                time.sleep(random.uniform(0.2, 1.0))
                self.sendProgressMessage(self.main.dataTransport, filedata, "waiting to convert")


                self.addConvertItem(entryData)
                self.printMessage("[" + self.name + "] Done downloading, now converting ...")
            # self.printMessage(d['filename'])
    def stop(self):
        self.add('STOP')
    def add(self,item):
        self.printMessage("adding:%s" % item)
        self.downloadQueue.put(item)
    def addConvertItem(self, item):
        self.printMessage("adding:%s" % item)
        self.convertQueue.put(item)
    def run(self):
        self.printMessage("Process is running:%s" % self.name)
        while self.isRunning:
            try:
                self.data = self.downloadQueue.get()
                if self.data is 'STOP':
                    break

                #     splitalbum download only downloads one file. Once it is done, that one file should be sent to the
                #   converter workers to be split up. But in order to do so, it needs to have the track information for all the other tracks.
                #   at this point, it only has information about the current track. might need a different download worker to do thisg

                self.main.params['plexrun'] = False
                time.sleep(0.3)
                # self.data is now self.addvideoItem Item
                self.playListData = self.data['playlistData']
                self.playlistItem = self.data['playlistItem']
                payload = self.data['payload']

                # payload['ydl_opts']
                self.printMessage("[" + self.name + "] Downloading:%s" % payload['download']['current']['url'])
                # print(payload['download']['current']['ydl_opts'])
                options = payload['download']['current']['ydl_opts'].copy()
                options['progress_hooks'] = [self._download_hook]

                time.sleep(0.5)
                retries = 3

                for i in range(retries):
                    with youtube_dl.YoutubeDL(options) as ydl:
                        try:
                            # self.printMessage("downloading")


                            ydl.download([payload['download']['current']['url']])
                            break
                        except (youtube_dl.utils.DownloadError, youtube_dl.utils.ContentTooShortError,
                                youtube_dl.utils.ExtractorError) as e:
                            # self.printMessage(e)
                            # file failed for some reason. Still add it to the result table as has been processed but
                            # failed with some error message

                            if i == (retries-1):
                                self.printMessage("[ERROR] failed. Cannot download file. Try again later")
                                self.sendProgressMessage(self.main.dataTransport, payload,
                                                         "failed:" + self.escape_string(str(e)))
                            else:
                                self.printMessage("[ERROR] failed. trying again. Attempt:" + str(i) + "/" + str(retries))
                                self.sendProgressMessage(self.main.dataTransport, payload, "[WARNING]. Retry attempt:" + str(i) + "/" + str(retries))
                            time.sleep(random.uniform(1.0, 2.0))
                            continue

                self.downloadQueue.task_done()
                time.sleep(0.3)
            except KeyboardInterrupt:
                break

        self.printMessage("Process is exiting:%s" % self.name)