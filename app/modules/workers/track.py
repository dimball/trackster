from __future__ import print_function
from __future__ import unicode_literals
import threading
import uuid
from common.utility import Utility
class Worker(threading.Thread, Utility):
    def __init__(self, main, params):
        threading.Thread.__init__(self)
        self.params = params
        self.filter = params['filter']
        self.setName("video worker")
        self.isRunning = True
        self.videoQueue = main.videoQueue
        self.downloadQueue = main.DownloadQueue
        self.dataTransport = main.dataTransport
        self.main = main

    def stop(self):
        # poison pill
        self.isRunning = False
        self.add('STOP')
    def addSplitAlbumItem(self, internalId, track, artist, album, counter, offset):
        tracknumber = ("{0:02d}").format(counter)
        title = track['mbtrack']['title']

        payload = self.create_payload(['results', 'row'])
        payload['results']['searchterm'] = artist + " - " + title
        payload['row']['tracknumber'] = tracknumber
        internal_videoId = str(uuid.uuid4())
        ydl_opts = {'format': 'bestaudio/best',
                    'outtmpl': self.params['folder'][
                                   'incomplete'] + "/" + artist + "/" + artist + " - " + album + "/" + internalId + "@" + internal_videoId + '.%(ext)s', }

        payload = self.create_payload(
            ['title.video', 'musicbrainz', 'thumbnail', 'download.video', 'playlist.video', 'row'])
        payload['id']['internal'] = internalId
        payload['id']['video'] = internal_videoId

        payload['musicbrainz']['artist'] = artist
        payload['musicbrainz']['title'] = album
        payload['musicbrainz']['duration'] = track['mbtrack']['duration']

        payload['title']['video']['original'] = self.escape_string(title)
        payload['title']['video']['track'] = self.escape_string(title)

        payload['download']['current']['ydl_opts'] = ydl_opts
        payload['download']['original']['ydl_opts'] = ydl_opts
        payload['playlist']['title'] = self.escape_string(artist + " - " + album)

        payload['row']['status'] = "queued"
        payload['row']['selected'] = True
        payload['row']['modified'] = False
        payload['row']['tracknumber'] = tracknumber

        payload['row']['duration'] = track['mbtrack']['duration']




        payload['row']['offset']['seconds'] = offset
        timeObj = self.durationToHHMMSS(payload['row']['offset']['seconds'])
        timeString = timeObj['hour'] + ":" + timeObj['minute'] + ":" + timeObj['second']
        payload['row']['offset']['formatted'] = timeString
        self.dataTransport.put(self.createDataItem('server/add/video', payload))
        offset = offset+payload['row']['duration']['seconds']
        return offset


    def addTrackItem(self, internalId, track, artist, album, counter):
        tracknumber = ("{0:02d}").format(counter)
        title = track['mbtrack']['title']

        # do a search on youtube, and get back the best result
        payload = self.create_payload(['results', 'row'])
        payload['results']['searchterm'] = artist + " - " + title
        payload['row']['tracknumber'] = tracknumber
        payload['id']['internal'] = internalId
        # search_results = self.select_by_id(self.dbsearch, payload['results']['searchterm'], 'search', 'searchTerm')
        search_results = self.main.getYoutubeResults(payload, self.dbsearch)

        try:
            self.printMessage("Results in search:" + str(len(search_results['results']['data'])))
        except:
            pass
        # print(search_results)
        search = ''
        currentTrackDuration = track['mbtrack']['duration']['seconds']
        # print("Duration is:" + str(currentTrackDuration))
        if currentTrackDuration == 0:
            for searchVid in search_results['results']['data']:
                # print(searchVid)
                if 'id' in searchVid:
                    search = searchVid
                    break
        else:
            # get the result that has the lowest difference in length found on musicbrainz.
            currentValue = 999999
            # print(search_results['results']['data'])
            # search only the first 10
            counter = 0
            for searchVid in search_results['results']['data']:

                # print(searchVid['results']['duration']['seconds'])
                if searchVid['results']['duration']['seconds'] != '':
                    checkSeconds = abs(currentTrackDuration-int(searchVid['results']['duration']['seconds']))
                    if checkSeconds < currentValue:
                        currentValue = checkSeconds
                        search = searchVid
                    if counter == self.params['compare_yt_videos']:
                        break
                else:
                    self.printMessage("SearchVid does not have a valid duration. Skipping search vid element")
                    # print(currentTrackDuration)
                    # print(searchVid['results']['duration'])
                    # pass

                counter += 1


        if search == '':
            # print(len(search_results['results']['data']))
            self.printMessage("No results from youtube...")
        else:
            videoId = search['download']['current']['videoId']
            thumbnailUrl = search['thumbnail']['current']['default']
            thumbnailLargeUrl = search['thumbnail']['current']['large']
            # timeObj = item['duration']

            internal_videoId = str(uuid.uuid4())
            # print(self.params['folder'][
            #           'incomplete'] + "/" + artist + "/" + artist + " - " + album + "/" + internalId + "@" + internal_videoId + '.%(ext)s')
            ydl_opts = {'format': 'bestaudio/best',
                        'outtmpl': self.params['folder']['incomplete'] + "/" + artist + "/" + artist + " - " + album + "/" + internalId + "@" + internal_videoId + '.%(ext)s', }


            payload = self.create_payload(['title.video', 'musicbrainz', 'thumbnail', 'download.video', 'playlist.video', 'row'])
            payload['id']['internal'] = internalId
            payload['id']['video'] = internal_videoId
            payload['musicbrainz']['artist'] = artist
            payload['musicbrainz']['title'] = album
            payload['musicbrainz']['duration'] = search['results']['duration']

            payload['title']['video']['original'] = self.escape_string(title)

            # only set the youtube property if the user has manually changed from the original youtube video
            # if the youtube video is the same as the original, then remove the value

            payload['title']['video']['track'] = self.escape_string(title)
            payload['title']['video']['youtube'] = self.escape_string(search['title']['video']['youtube'])

            payload['thumbnail']['original']['default'] = self.escape_string(thumbnailUrl)
            payload['thumbnail']['original']['large'] = self.escape_string(thumbnailLargeUrl)

            payload['thumbnail']['current']['default'] = self.escape_string(thumbnailUrl)
            payload['thumbnail']['current']['large'] = self.escape_string(thumbnailLargeUrl)
            #
            payload['download']['current']['url'] = self.params['baseurl'] + videoId
            payload['download']['current']['videoId'] = videoId
            payload['download']['current']['ydl_opts'] = ydl_opts
            # payload['download']['current']['target_output'] = target_output

            #
            payload['download']['original']['url'] = self.params['baseurl'] + videoId
            payload['download']['original']['videoId'] = videoId
            payload['download']['original']['ydl_opts'] = ydl_opts
            # payload['download']['original']['target_output'] = target_output

            payload['playlist']['title'] = self.escape_string(artist + " - " + album)

            payload['row']['status'] = "queued"
            payload['row']['selected'] = True
            payload['row']['modified'] = False
            payload['row']['tracknumber'] = tracknumber

            payload['row']['duration'] = track['mbtrack']['duration']

            self.dataTransport.put(self.createDataItem('server/add/video', payload))
    def addVideoItem(self, internalID, item, artist, album, counter):
        if artist == "-1":
            artist = "Various Artists"
        if album == "-1":
            album = "Mix"

        tracknumber = ("{0:02d}").format(counter)
        title = item['snippet']['title']
        videoId = item['snippet']['resourceId']['videoId']
        thumbnailUrl = item['snippet']['thumbnails']['default']['url']
        thumbnailLargeUrl = item['snippet']['thumbnails']['high']['url']
        timeObj = item['duration']

        internal_videoId = str(uuid.uuid4())

        filtered_title = self.filter_string(self.escape_string(title), self.filter)

        filtered_title = self.filter_string_input(filtered_title, [tracknumber, album])



        ydl_opts = {'format': 'bestaudio/best',
                    'outtmpl': self.params['folder']['incomplete'] + "/" + artist + "/" + artist + " - " + album + "/" + internalID + "@" + internal_videoId + '.%(ext)s', }

        payload = self.create_payload(['title.video', 'thumbnail', 'download.video', 'playlist.video', 'row'])
        payload['id']['internal'] = internalID
        payload['id']['video'] = internal_videoId

        payload['title']['video']['original'] = self.escape_string(title)

        # only set the youtube property if the user has manually changed from the original youtube video
        # if the youtube video is the same as the original, then remove the value

        # payload['title']['video']['youtube'] = self.escape_string(title)
        payload['title']['video']['track'] = self.escape_string(filtered_title)

        payload['thumbnail']['original']['default'] = self.escape_string(thumbnailUrl)
        payload['thumbnail']['original']['large'] = self.escape_string(thumbnailLargeUrl)

        payload['thumbnail']['current']['default'] = self.escape_string(thumbnailUrl)
        payload['thumbnail']['current']['large'] = self.escape_string(thumbnailLargeUrl)

        payload['download']['current']['url'] = self.params['baseurl'] + videoId
        payload['download']['current']['videoId'] = videoId
        payload['download']['current']['ydl_opts'] = ydl_opts
        # payload['download']['current']['target_output'] = self.params['folder']['output'] + playlistTitle + "/" + internalID + "@" + internal_videoId + '.%(ext)s'

        payload['download']['original']['url'] = self.params['baseurl'] + videoId
        payload['download']['original']['videoId'] = videoId
        payload['download']['original']['ydl_opts'] = ydl_opts

        payload['playlist']['title'] = self.escape_string(album)


        payload['row']['status'] = "queued"
        payload['row']['selected'] = True
        payload['row']['modified'] = False
        payload['row']['tracknumber'] = tracknumber
        payload['row']['duration'] = timeObj

        self.dataTransport.put(self.createDataItem('server/add/video', payload))
    def add(self,payload):
        # self.printMessage("adding:%s" % payload)
        self.videoQueue.put(payload)
    def run(self):
        self.dbsearch = self.main.connectDB(self.params['folder']['dbsearch'])
        self.printMessage("Thread is running:%s" % self.getName())
        while self.isRunning:
            try:
                payload = self.videoQueue.get()

                if payload is 'STOP':
                    break
                if not self.isRunning:
                    break
                counter = 1
                progressCounter = 1
                if payload['playlist']['type'] == 'playlist':

                    for i in range(len(payload['items'])):
                        videoItem = payload['items'][i]

                        if videoItem['snippet']['title'] != "Deleted video" and \
                                        'blocked' not in videoItem['snippet']['title'] and \
                                'Private video' not in videoItem['snippet']['title'] and \
                                'duration' in videoItem:
                            self.addVideoItem(payload['id']['internal'],
                                              videoItem,
                                              payload['title']['playlist']['artist'],
                                              payload['title']['playlist']['album'],
                                              counter)
                        else:
                            reason = None
                            if videoItem['snippet']['title'] == "Deleted video":
                                reason = "deleted video"
                            elif 'blocked' in videoItem['snippet']['title']:
                                reason = "blocked video"
                            elif 'Private video' in videoItem['snippet']['title']:
                                reason = "private video"
                            elif 'duration' not in videoItem:
                                reason = "no timing info in video. Possible cause: Video does not exist"

                            self.printMessage("Not adding:" + videoItem['snippet']['title'] +  " reason:" + reason)



                        customPayload = self.create_payload(['custom'])
                        customPayload['id']['internal'] = payload['id']['internal']
                        customPayload['custom']['progress'] = progressCounter / len(payload['items']) * 100
                        customPayload['custom']['reset'] = True
                        customPayload['custom']['message'] = "loading track information"
                        # print(customPayload['custom']['progress'])
                        self.dataTransport.put(self.createDataItem('server/result/import', customPayload))
                        counter += 1

                        progressCounter += 1

                elif payload['playlist']['type'] == 'artistalbum':
                    self.printMessage('creating artist album data type')

                    tracklist = self.main.getMbTrackResults(
                        payload,
                        self.dbsearch
                    )
                    id = payload['id']['internal']

                    if tracklist != None:
                        for track in tracklist:
                            self.addTrackItem(
                                id,
                                track,
                                payload['title']['playlist']['artist'],
                                payload['title']['playlist']['album'],
                                counter
                            )

                            customPayload = self.create_payload(['custom'])
                            customPayload['id']['internal'] = payload['id']['internal']
                            customPayload['custom']['progress'] = (progressCounter/len(tracklist)*100)
                            customPayload['custom']['reset'] = True
                            customPayload['custom']['message'] = "loading track information"
                            self.dataTransport.put(self.createDataItem('server/result/import', customPayload))
                            progressCounter += 1
                            counter += 1


                        self.printMessage("track import completed")
                    else:
                        self.printMessage("track list returned None. May be due to connection error to Musicbrainz server")
                elif payload['playlist']['type'] == 'splitalbum':
                    self.printMessage('creating split album data type')
                    tracklist = self.main.getMbTrackResults(
                        payload,
                        self.dbsearch
                    )



                    # this should just create the track entries with track number, duration, and title
                    # this should be enough to create where the output should be

                    offset = 0
                    for track in tracklist:
                        offset = self.addSplitAlbumItem(
                            payload['id']['internal'],
                            track,
                            payload['title']['playlist']['artist'],
                            payload['title']['playlist']['album'],
                            counter,
                            offset

                        )

                        customPayload = self.create_payload(['custom'])
                        customPayload['id']['internal'] = payload['id']['internal']
                        customPayload['custom']['progress'] = (progressCounter / len(tracklist) * 100)
                        customPayload['custom']['reset'] = True
                        customPayload['custom']['message'] = "loading track information"
                        self.dataTransport.put(self.createDataItem('server/result/import', customPayload))
                        progressCounter += 1
                        counter += 1

                    playlistPayload = self.create_payload(['playlist.playlist'])
                    playlistPayload['id']['internal'] = payload['id']['internal']
                    playlistPayload['playlist']['duration']['seconds'] = offset
                    timeObj = self.durationToHHMMSS(offset)
                    timeString = timeObj['hour'] + ":" + timeObj['minute'] + ":" + timeObj['second']
                    playlistPayload['playlist']['duration']['formatted'] = timeString

                    self.dataTransport.put(self.createDataItem('server/update/splitalbum/duration', playlistPayload))

                    self.printMessage("track import completed")

                #     update the playlist with the total album duration


                self.videoQueue.task_done()

            except KeyboardInterrupt:
                break
        self.printMessage("Thread is exiting:%s" % self.getName())
