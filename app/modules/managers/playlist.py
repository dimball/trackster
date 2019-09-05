from __future__ import print_function
from __future__ import unicode_literals
import json
import requests
import threading
from urllib.parse import urlparse
from urllib.parse import parse_qsl
import uuid
from modules.common.utility import Utility
class Manager(threading.Thread, Utility):
    def __init__(self, main, params):
        threading.Thread.__init__(self)
        self.params = params
        self.filter = params['filter']
        self.setName("Playlist manager")
        self.isRunning = True
        self.PlaylistQueue = main.PlaylistQueue
        self.videoQueue = main.videoQueue
        # self.downloadQueue = main.DownloadQueue
        self.dataTransport = main.dataTransport
        self.main = main

            # self.main.connectDB(DBSEARCH)
    def stop(self):
        # poison pill
        self.isRunning = False
        self.add('STOP')

    def addPlaylistEntry(self, ID, artist, album, numItems, playlisttype):
        internalID = str(uuid.uuid4())
        # print("artist:" + artist)
        if playlisttype == 'splitalbum':
            video_id = str(uuid.uuid4())
            payload = self.create_payload(['title.playlist', 'download.splitalbum', 'playlist.playlist', 'row'])
            payload['playlist']['videoItem'] = self.create_payload(['title.video', 'musicbrainz', 'thumbnail', 'download.video', 'playlist.video', 'row'])
            payload['playlist']['videoItem']['id']['internal'] = internalID
            payload['playlist']['videoItem']['id']['video'] = video_id

            artistalbum = artist + '-' + album
            formattype = 'bestaudio/best',
            outtmpl = self.params['folder']['incomplete'] + '/' + artist + '/' + artistalbum + '/' + \
                   internalID + '@' + video_id + '.%(ext)s'

            ydl_opts = {'format':formattype,
                        'outtmpl':outtmpl
            }
            payload['playlist']['videoItem']['download']['current']['ydl_opts'] = ydl_opts
        else:
            payload = self.create_payload(['title.playlist', 'download.playlist', 'playlist.playlist', 'row'])

        payload['id']['internal'] = internalID
        payload['download']['playlistId'] = ID
        payload['title']['playlist']['artist'] = self.escape_string(artist)
        payload['title']['playlist']['album'] = self.escape_string(album)
        payload['playlist']['progress'] = 0
        payload['playlist']['totalItems'] = numItems
        payload['playlist']['type'] = playlisttype


        payload['items'] = []
        payload['index'] = {}

        self.dataTransport.put(self.createDataItem('server/add/playlist', payload))
        return internalID
    def add(self,payload):
        # self.printMessage("adding:%s" % payload)
        self.PlaylistQueue.put(payload)
    def run(self):
        # self.dbsearch = self.main.connectDB(DBSEARCH)
        self.printMessage("Thread is running:%s" % self.getName())
        while self.isRunning:

            try:
                payload = self.PlaylistQueue.get()
                if payload is 'STOP':
                    break
                if not self.isRunning:
                    break

                if payload['playlist']['type'] == 'playlist':

                    playlistUrl = payload['playlist']['url']
                    videoID = ""
                    parsed = urlparse(playlistUrl)
                    UrlParams = parse_qsl(parsed.query)
                    isPlaylistUrl = False
                    for x, y in UrlParams:
                        if x == 'list':
                            playlistUrl = y
                            isPlaylistUrl = True
                        if x == 'v':
                            videoID = y

                    if not isPlaylistUrl:
                        self.printMessage("Not a valid URL:%s" % videoID)
                        # internalId = self.addPlaylistEntry(playlistUrl, 'Various_Artists', 1)
                        # self.addVideoItem(internalId, item, 0)
                        # # add only one file
                        # ydl_opts = {'format': 'bestaudio/best',
                        #              'outtmpl': './download/Various_Artists/01 - ' + title + '.%(ext)s',}
                        # self.params['videoId'] = videoID
                        # self.printMessage(self.params['videoId'])
                        # time.sleep(0.2)
                        # self.addDownloadItem(self.params)

                    else:
                        # process playlist

                        # self.params['playlistId'] = playlistUrl
                        itemsParameters = "nextPageToken,items(id,snippet(resourceId(videoId),title, thumbnails))&part=snippet"
                        playlistParameters = "items(snippet(localized(title)))"
                        playlistAPIurl = "https://www.googleapis.com/youtube/v3/playlists?part=snippet&id=" + \
                                         playlistUrl + "&key=" + self.params['ApiKey'] + "&fields=" + \
                                         playlistParameters
                        itemsUrl = "https://www.googleapis.com/youtube/v3/playlistItems?&key=" + self.params['ApiKey'] + \
                                   "&playlistId=" + playlistUrl + "&fields=" + itemsParameters + \
                                   "&maxResults=50"
                        try:
                            PlayListResponse = requests.get(playlistAPIurl)
                            json_data_playList = json.loads(PlayListResponse.text)



                            ItemsResponse = requests.get(itemsUrl)
                            json_data_items = json.loads(ItemsResponse.text)
                            # for iIndex in range(len(json_data_items['items'])):
                            #     videoItem =
                            json_data_items = self.InsertTimeData(json_data_items, self.params['ApiKey'])



                            playlistItems = json_data_items['items']

                            if 'nextPageToken' in json_data_items:
                                while 'nextPageToken' in json_data_items:
                                    itemsUrl = "https://www.googleapis.com/youtube/v3/playlistItems?&key=" + self.params['ApiKey'] + \
                                               "&playlistId=" + playlistUrl + "&pageToken=" + json_data_items['nextPageToken'] + \
                                               "&fields=" + itemsParameters + "&maxResults=50"
                                    ItemsResponse = requests.get(itemsUrl)


                                    json_data_items = json.loads(ItemsResponse.text)
                                    json_data_items = self.InsertTimeData(json_data_items, self.params['ApiKey'])
                                    playlistItems += (json_data_items['items'])

                            payload['playlist']['title'] = self.filter_string(json_data_playList['items'][0]['snippet']['localized']['title'], self.filter)
                            payload['title']['playlist']['album'] = self.filter_string(json_data_playList['items'][0]['snippet']['localized']['title'], self.filter)
                            payload['title']['playlist']['artist'] = '-1'
                            # add an item to the datastructure
                            # the datastructure should be assembled in the main thread using a queue as a transport mechanism

                            payload['id']['internal'] = self.addPlaylistEntry(playlistUrl, "-1",  payload['title']['playlist']['album'], len(playlistItems), payload['playlist']['type'])
                            # send to a the video thread
                            payload['items'] = playlistItems

                            self.videoQueue.put(payload)
                        except requests.exceptions.ConnectionError:
                            self.printMessage("Could not connect to internet")

                elif payload['playlist']['type'] == 'artistalbum':
                    # print('creating artist album data type')
                    artist = payload['title']['playlist']['artist']
                    album = payload['title']['playlist']['album']

                    payload['id']['internal'] = self.addPlaylistEntry(payload['musicbrainz']['id'], artist, album, 0, payload['playlist']['type'])
                    self.videoQueue.put(payload)
                    self.printMessage("Created playlist")
                elif payload['playlist']['type'] == 'splitalbum':
                    artist = payload['title']['playlist']['artist']
                    album = payload['title']['playlist']['album']


                    # need to find the total length of the album
                    # need to find a youtube video that has the artist and album and a similar length. Possible that it cannot have a shorter length than the album length
                    # can only find the total length of the album

                    payload['id']['internal'] = self.addPlaylistEntry(payload['musicbrainz']['id'], artist, album, 0,
                                                                      payload['playlist']['type'])
                    self.videoQueue.put(payload)
                    self.printMessage("Created playlist for splitalbum")



                self.PlaylistQueue.task_done()

            except KeyboardInterrupt:
                break
        self.printMessage("Thread is exiting:%s" % self.getName())