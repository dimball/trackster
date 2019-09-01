from __future__ import print_function
from __future__ import unicode_literals
from multiprocessing.context import Process
import stat
from subprocess import Popen, PIPE
import os
from mutagen.easyid3 import EasyID3
import re  # Regular expression library
import time
from common.utility import Utility
FFMPEG_CMD = ['ffmpeg']
EasyID3.RegisterTextKey('comment', 'COMM')
class Worker(Process, Utility):
    def __init__(self, main, id):
        Process.__init__(self)
        self.convertQueue = main.ConvertQueue
        self.name = "Converter " + str(id)
        self.isRunning = True
        self.dataTransport = main.dataTransport
        self.main = main
        self.params = main.params
        self.filter = main.params['filter']
    def set_id3(self, file, playlistData):

        fileData = self.GetDataFromFilename(str(file))
        tagFile = EasyID3(file)

        videoData = self.getdata('video', playlistData, fileData)
        playlistInfo = self.getdata('playlist', playlistData, fileData)
        tagFile['tracknumber'] = videoData['row']['tracknumber']
        tagFile['title'] = self.unescape_string(videoData['title']['video']['track'])

        if self.unescape_string(playlistInfo['title']['playlist']['artist']) == '-1':
            tagFile['artist'] = "Various Artists"
        else:
            tagFile['artist'] = self.unescape_string(playlistInfo['title']['playlist']['artist'])

        if self.unescape_string(playlistInfo['title']['playlist']['album']) == '-1':
            tagFile['album'] = "Mix"
        else:
            tagFile['album'] = self.unescape_string(playlistInfo['title']['playlist']['album'])

        outputfile = videoData['row']['tracknumber'] + " - " + self.unescape_string(videoData['title']['video']['track'])
        outputfile = re.sub("\s\s+", " ", outputfile)

        if outputfile[-1] == " ":
            outputfile = outputfile[:-1] + fileData['ext']
        else:
            outputfile = outputfile + fileData['ext']
        self.printMessage("[" + self.name + " - Tagging]: %s" % fileData['basepath'] + "/" + outputfile)

        tagFile['comment'] = "Converted from youtube using Trackster"
        tagFile.save()
        self.printMessage("[" + self.name + " - Tagging] Complete:%s" % fileData['basepath'] + "/" + outputfile)
        try:
            os.rename(file, fileData['basepath'] + "/" + outputfile)
        except OSError as e:
            self.printMessage("Could not rename file: " + file + "-> " + fileData['basepath'] + "/" + outputfile)
            self.printMessage(e)

        self.sendProgressMessage(self.main.dataTransport, fileData, "complete")
    def add(self, item):
        self.printMessage("adding:%s" % item)
        self.convertQueue.put(item)
    def stop(self):
        self.add('STOP')
    def execute_ffmpeg(self, args):

        try:
            command = FFMPEG_CMD + args
            # self.printMessage('Calling: ' + str(self.command))
            pipe = Popen(command, stderr=PIPE)
            pipe.stderr.read()
            pipe.terminate()
            self.printMessage("[{}] Conversion complete".format(self.name))
            return True
        except e:
            self.printMessage("[{}}] ERROR could not complete conversion:{}".format(self.name, e))
            return False
    def run(self):
        self.printMessage("Process is running:%s" % self.name)
        while self.isRunning:
            try:
                data = self.convertQueue.get()
                print(data)
                if data == "STOP":
                    self.isRunning = False
                    break

                print("running")
                filename = data['filename']
                playlistData = data['playlistData']

                playlistItem = data['playlistItem']


                # at this point, the converter should know that this is a split album type and split the file at a specified place

                self.printMessage("[" + self.name + "] Converting file:%s" % filename)
                # splitting the extension and filename
                Basepath = os.path.basename(filename)
                file, ext = os.path.splitext(Basepath)

                path = (os.path.dirname(filename))


                # parentfolder = os.path.basename(os.path.abspath(os.path.join(outputFileName, "../")))
                # grandparentfolder = os.path.basename(os.path.abspath(os.path.join(outputFileName, "../..")))

                # target_outputFileName = self.params['folder']['output'] + '/' + \
                #                         grandparentfolder + \
                #                         "/" + parentfolder + \
                #                         "/" + file + '.mp3'

                # remove an existing file


                if playlistItem['playlist']['type'] == 'splitalbum':
                #     set the ffmpeg arguments to split the file using some time arguments

                    # fileData = self.GetDataFromFilename(str(file))
                    videoData = data['videoItem']


                    outputFileName = path + '/' + videoData['row']['tracknumber'] + '-' + videoData['title']['track'] + '.mp3'

                    if os.path.exists(outputFileName):
                        os.remove(outputFileName)
                    starttime = time.strftime('%H:%M:%S', time.gmtime(videoData['row']['duration']['offset']['seconds']+videoData['row']['duration']['silence']['seconds']))
                    endtime = time.strftime('%H:%M:%S', time.gmtime(videoData['row']['duration']['offset']['seconds']+videoData['row']['duration']['seconds']))
                    ffmpeg_args = ['-i',
                                filename,
                                '-acodec',
                                'copy',
                                '-ss ' + starttime,
                                '-to ' + endtime,
                               outputFileName]

                    self.sendProgressMessage(self.main.dataTransport, self.GetDataFromFilename(outputFileName), "converting")
                    if self.execute_ffmpeg(ffmpeg_args):
                        filedata = self.GetDataFromFilename(outputFileName)
                        if os.path.exists(filedata['basepath'] + "/" + filedata['filename'] + ".temp" + filedata['ext']):
                            os.remove(filedata['basepath'] + "/" + filename + ".temp" + filedata['ext'])
                        elif os.path.exists(filename):
                            os.remove(filename)
                        self.set_id3(outputFileName, playlistData)
                    else:
                        self.sendProgressMessage(self.main.dataTransport, self.GetDataFromFilename(outputFileName),
                                             "failed split conversion")

                else:

                    outputFileName = path + '/' + file + '.mp3'
                    if os.path.exists(outputFileName):
                        os.remove(outputFileName)



                    ffmpeg_args = ['-i',
                                        filename,
                                        '-q:a',
                                        '0',
                                        '-map',
                                        'a',
                                        outputFileName]
                    self.sendProgressMessage(self.main.dataTransport, self.GetDataFromFilename(outputFileName), "converting")

                    if self.execute_ffmpeg(ffmpeg_args):
                        # remove the old unconverted audio file
                        # do not remove this if this is a split album as other converters may be still using it
                        filedata = self.GetDataFromFilename(outputFileName)


                        if os.path.exists(filedata['basepath'] + "/" + filedata['filename'] + ".temp" + filedata['ext']):
                            os.remove(filedata['basepath'] + "/" + filename + ".temp" + filedata['ext'])
                        elif os.path.exists(filename):
                            os.remove(filename)

                        # set the permissions on the file
                        os.chmod(outputFileName,
                                 stat.S_IWGRP | stat.S_IRGRP | stat.S_IRUSR | stat.S_IWUSR | stat.S_IROTH | stat.S_IWOTH)


                        self.set_id3(outputFileName, playlistData)
                    else:
                        self.sendProgressMessage(self.main.dataTransport, self.GetDataFromFilename(outputFileName),
                                                 "failed conversion")


                self.convertQueue.task_done()
                time.sleep(0.1)

            except KeyboardInterrupt:
                break
        self.printMessage("Process is exiting:%s" % self.name)