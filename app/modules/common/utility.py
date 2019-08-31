from __future__ import print_function
from __future__ import unicode_literals
import json
import requests
import os
import uuid
import musicbrainzngs
import sys
import time
import datetime
import random
DEBUG = True
class Utility():
    # path utils
    def SetDevMode(self):
        production_main = '/code/app/server.py'

        production_folder = {
            'complete': '/code/download',
            'incomplete': '/code/incomplete',
            'dbfile': '/code/app/db/ytdownloader.db',
            'dbfilter': '/code/app/db/ytfilter.db',
            'dbsearch': '/code/app/db/ytsearch.db',
            'mode': 'production'
        }
        dev_folder = {
            'complete': './download',
            'incomplete': './incomplete',
            'dbfile': './db/ytdownloader.db',
            'dbfilter': './db/ytfilter.db',
            'dbsearch': './db/ytsearch.db',
            'mode': 'dev'
        }
        if os.path.exists(production_main):
            self.printMessage("PRODUCTION mode")
            return production_folder
        else:
            self.printMessage("DEV mode")
            return dev_folder
    # data utils
    def create_payload(self, parts = ['title.video', 'title.playlist', 'thumbnail', 'download.video','download.playlist', 'playlist.playlist', 'playlist.video', 'row']):
        payload = {}
        payload['id'] = {
            'internal': '',
            'video': '',
            'filter': ''
        }
        if 'title.video' in parts:
            payload['title'] = {
                'video': {
                    'original': '',
                    'track': '',
                    'youtube': ''
                }
            }
        if 'title.playlist' in parts:
            payload['title'] = {
                'playlist': {
                    'album': '',
                    'artist': ''
                },
                'video': {
                    'original': '',
                    'youtube': ''
                }
            }
        if 'thumbnail' in parts:
            payload['thumbnail'] = {
                    'original': {
                        'default': '',
                        'large': ''
                    },
                    'current': {
                        'default': '',
                        'large': ''
                    }
            }
        if 'download.video' in parts:
            payload['download'] = {
                    'original': {
                        'url': '',
                        'ydl_opts': '',
                        'videoId': ''
                    },
                    'current': {
                        'url': '',
                        'ydl_opts': '',
                        'videoId': ''
                    }
                 }
        if 'download.playlist' in parts:
            payload['download'] = {
                'playlistId': ''
            }
        if 'download.splitalbum' in parts:
            payload['download'] = {
                'playlistId': '',
                'videoItem': ''
            }
        if 'playlist.video' in parts:
            payload['playlist'] = {
                    'title': ''
            }
        if 'playlist.playlist' in parts:
            payload['playlist'] = {
                'progress': '-1',
                'import_progress': '-1',
                'totalItems': '',
                'type': '',
                'url': '',
                'duration': {
                    'seconds': '',
                    'formatted': ''
                }
            }
        if 'row' in parts:
            payload['row'] = {
                    'status': '',
                    'selected': '',
                    'modified': '',
                    'tracknumber': '',

                    'duration': {
                        'seconds': 0,
                        'formatted': '',
                        'original' : {
                            'seconds': 0
                        }

                    },
                    'offset': {
                        'seconds': 0,
                        'formatted': '',
                    },
                    'silence': {
                        'seconds': 0
                    }
            }
        if 'results' in parts:
            payload['results'] = {
                'description': '',
                'index':'',
                'searchterm':'',
                'data':'',
                'itemrange':[],
                'duration': {
                    'seconds':'',
                    'formatted':''
                },
                'requestedby':''

            }
        if 'musicbrainz' in parts:
            payload['musicbrainz'] = {
                'score':'',
                'title': '',
                'artist': '',
                'released': {
                    'date':'',
                    'seconds': 0
                },

                'id': '',
                'disambiguation': '',
                'trackcount':0,
                'tracks': []
            }
        if 'musicbrainz.track' in parts:
            payload['mbtrack'] = {
                'title': '',
                'duration': {
                    'seconds': '',
                    'formatted': '',
                    'original': {
                        'seconds': 0
                    }
                }
            }
        if 'custom' in parts:
            payload['custom'] = {}
        if 'filter' in parts:
            payload['filter'] = {
                'key':'',
                'value':''
            }
        return payload
    def createDataItem(self, type, payload):
        data = {
            'type': type,
            'payload': payload
        }
        return data
    def setdata(self, type, data, payload):
        if type == 'playlist':
            data['items'].append(payload)
            data['index'][payload['id']['internal']] = len(data['items']) - 1
        elif type == 'video':
            playlistItem = self.getdata('playlist', data, payload)
            playlistItem['items'].append(payload)
            playlistItem['index'][payload['id']['video']] = len(playlistItem['items']) - 1
            # elif type == 'recording':
            #     print('adding recording')
    def getdata(self, type, data, payload):
        if type == 'playlist':
            id = payload['id']['internal']

            index = data['index'][id]

            payload = data['items'][index]
            return payload
        elif type == 'video':
            playlistItem = self.getdata('playlist', data, payload)
            index = playlistItem['index'][payload['id']['video']]
            payload = playlistItem['items'][index]
            return payload
            # elif type == 'recording':
            #
            #     payload = 'test'
            #     return payload
    def removedata(self, type, data, payload):
        if type == 'playlist':
            index = data['index'][payload['id']['internal']]
            del data['items'][index]
            del data['index'][payload['id']['internal']]
            # reindex the index property

            for i in range(len(data['items'])):
                id = data['items'][i]['id']['internal']
                data['index'][id] = i
    # musicbrainz
    def getunixseconds(self, datestamp):
        timesplit = datestamp.split("-")
        timeobj = None
        if len(timesplit) == 1:
            timeobj = datetime.datetime.strptime(datestamp, "%Y").timetuple()
        elif len(timesplit) == 2:
            timeobj = datetime.datetime.strptime(datestamp, "%Y-%m").timetuple()
        elif len(timesplit) == 3:
            timeobj = datetime.datetime.strptime(datestamp, "%Y-%m-%d").timetuple()

        # print(timeobj)
        return time.mktime(timeobj)
    def show_release_details(self, rel):
        """Print some details about a release dictionary to stdout.
        """
        # "artist-credit-phrase" is a flat string of the credited artists
        # joined with " + " or whatever is given by the server.
        # You can also work with the "artist-credit" list manually.

        if 'disambiguation' in rel:
            print("{} ({}), by {}".format(rel['title'], rel['disambiguation'], rel["artist-credit-phrase"]))
        else:
            print("{}, by {}".format(rel['title'], rel["artist-credit-phrase"]))

        if 'date' in rel and 'status' in rel:
            print("Released {} ({})".format(rel['date'], rel['status']))
        print("MusicBrainz ID: {}".format(rel['id']))

        # uncomment this to get the track results

        # print(rel)
        # time.sleep(random.uniform(0.1, 1.0))
        # trackresult = musicbrainzngs.search_recordings(reid=rel['id'])
        #
        # print(trackresult)
        # for recording in trackresult['recording-list']:
        #     print(recording['title'])
    def get_tracks(self, id):
        time.sleep(random.uniform(0.1, 1.0))
        try:
            dataArray = []
            trackresult = musicbrainzngs.search_recordings(reid=id)


            for recording in trackresult['recording-list']:
                payload = self.create_payload(['musicbrainz.track'])

                payload['mbtrack']['title'] = recording['title']
                # print(recording)
                if 'length' in recording:
                    duration = float(recording['length'])
                    # print(duration)
                    durationInSeconds = int(duration/1000)

                    timeObj = self.durationToHHMMSS(durationInSeconds)
                    timeString = timeObj['hour'] + ":" + timeObj['minute'] + ":" + timeObj['second']

                    payload['mbtrack']['duration'] = {
                        'seconds': durationInSeconds,
                        'formatted': timeString,
                        'original': {
                            'seconds': durationInSeconds
                        }
                    }
                dataArray.append(payload)

            return dataArray
        except musicbrainzngs.NetworkError:
            self.printMessage("Could not connect to musicbrainz server at:" + MBHOST)
            return None
    # def findTracklist(self, id):
    #     time.sleep(random.uniform(0.1, 1.0))
    #     tracklist = musicbrainzngs.search_recordings(reid=id)
    #     return tracklist['recording-list']
    def findArtistAlbum(self, artist, album):
        # Keyword arguments to the "search_*" functions limit keywords to
        # specific fields. The "limit" keyword argument is special (like as
        # "offset", not shown here) and specifies the number of results to
        # return.
        self.printMessage("searching for:" + artist + " " + album)
        result = musicbrainzngs.search_releases(artist=artist, release=album,
                                                limit=100)
        # print(result)
        # On success, result is a dictionary with a single key:
        # "release-list", which is a list of dictionaries.
        dataArray = []
        if not result['release-list']:
            sys.exit("no release found")
        counter = 0
        # print(result)
        for (idx, release) in enumerate(result['release-list']):
            # if release['ext:score'] > '0':
                # if counter == 100:
                #     break
            # print("match #{}:".format(idx + 1))

            payload = self.create_payload(['musicbrainz'])
            payload['musicbrainz']['score'] = release['ext:score']
            payload['musicbrainz']['title'] = release['title']
            if 'medium-list' in release:
                # print(len(release['medium-list']))
                for trackIndex in release['medium-list']:
                    if 'track-count' in trackIndex:
                        if trackIndex['track-count'] > 0:
                            payload['musicbrainz']['trackcount'] = trackIndex['track-count']
                            break

            payload['musicbrainz']['artist'] = release['artist-credit-phrase']

            if 'disambiguation' in release:
                payload['musicbrainz']['disambiguation'] = release['disambiguation']

            payload['musicbrainz']['id'] = release['id']
            if 'date' in release:
                payload['musicbrainz']['released']['date'] = release['date']
                payload['musicbrainz']['released']['seconds'] = self.getunixseconds(release['date'])
            # self.show_release_details(release)
            dataArray.append(payload)
            counter += 1

        return dataArray
    def findArtist(self, artist):
        artistresult = musicbrainzngs.search_artists(artist=artist, limit=100)
        results = []
        for res in artistresult['artist-list']:
            # if res['ext:score'] > '0':
            # print(res)
            payload = self.create_payload(['musicbrainz'])
            payload['musicbrainz']['score'] = res['ext:score']

            payload['musicbrainz']['artist'] = res['name']
            if 'disambiguation' in res:
                payload['musicbrainz']['disambiguation'] = res['disambiguation']

            payload['musicbrainz']['id'] = res['id']
            results.append(payload)

        return results
    def searchTimeData(self, videoIds, apikey):
        # videoIds = videoIds[:-1]
        searchAPIurl = "https://www.googleapis.com/youtube/v3/videos?id=" + videoIds + "&part=contentDetails&key=" + \
                       apikey
        # self.printMessage(searchAPIurl)
        videoDataResponse = requests.get(searchAPIurl)
        videoDataResponse = json.loads(videoDataResponse.text)

        return videoDataResponse
    # youtube
    def InsertTimeData(self, videoItemList, apikey):
        print("Inserting time data")
        videoIds = ""
        # print(videoItemList)
        if 'items' in videoItemList:
            if len(videoItemList['items'])<50:
                self.printMessage("Less than 50 items")
                snippetCounter = 0
                for searchVid in videoItemList['items']:
                    if 'snippet' in searchVid:
                        # self.printMessage("has snippet")
                        if 'resourceId' in searchVid['snippet']:
                            videoIds += searchVid['snippet']['resourceId']['videoId'] + ","
                        else:
                            if 'id' in searchVid:
                                # print(searchVid)
                                # print("checking video")
                                videoIds += searchVid['id']['videoId']
                                if snippetCounter < 49:
                                    videoIds += ","
                            else:
                                self.printMessage("No Id:" + searchVid['snippet']['title'])
                        snippetCounter += 1
                    else:
                        self.printMessage("No snippet:" + searchVid)

                videoIds = videoIds[:-1]
                # self.printMessage(videoIds)

                videoDataResponse = self.searchTimeData(videoIds, apikey)
                # self.printMessage("snippet counter:" + str(snippetCounter))

                # self.printMessage("video data response:" + str(len(videoDataResponse['items'])))
                # self.printMessage("video item list:" + str(len(videoItemList['items'])))

                # print(videoDataResponse)

                for itemIndex in range(len(videoDataResponse['items'])):
                    videoItem = videoDataResponse['items'][itemIndex]
                    id = (videoItem['id'])
                    durationInSeconds = self.durationToSeconds(videoItem['contentDetails']['duration'])
                    timeObj = self.durationToHHMMSS(durationInSeconds)
                    timeString = timeObj['hour'] + ":" + timeObj['minute'] + ":" + timeObj['second']

                    # find out what index this should be in as there is no guarantee that this is a one to one response
                    for listIndex in range(len(videoItemList['items'])):
                        checkVideoItem = videoItemList['items'][listIndex]
                        checkVideoId = None

                        if 'resourceId' in checkVideoItem['snippet']:
                            checkVideoId = checkVideoItem['snippet']['resourceId']['videoId']
                        elif 'id' in checkVideoItem:
                            checkVideoId = checkVideoItem['id']['videoId']

                        # print(checkVideoId)
                        if checkVideoId == id:
                            entry = videoItemList['items'][listIndex]

                            entry['duration'] = {
                                'seconds': durationInSeconds,
                                'formatted': timeString
                            }
            else:
                self.printMessage("More than 50 items")
                counter = 0
                # listCounter = 0
                for searchVid in videoItemList['items']:
                    if 'snippet' in searchVid:
                        videoIds += searchVid['snippet']['resourceId']['videoId']
                        if counter < 49:
                            videoIds += ","

                    else:
                        if 'id' in searchVid:
                            # print(searchVid)
                            # print("checking video")
                            videoIds += searchVid['id']['videoId']
                            if counter < 49:
                                videoIds += ","
                        else:
                            self.printMessage("No Id:" + searchVid['snippet']['title'])

                    if counter == 49:
                        # print(videoIds)
                        videoDataResponse = self.searchTimeData(videoIds, apikey)
                        # print(videoDataResponse)

                        for videoItem in videoDataResponse['items']:
                            id = (videoItem['id'])
                            durationInSeconds = self.durationToSeconds(videoItem['contentDetails']['duration'])
                            timeObj = self.durationToHHMMSS(durationInSeconds)
                            timeString = timeObj['hour'] + ":" + timeObj['minute'] + ":" + timeObj['second']

                            for listIndex in range(len(videoItemList['items'])):
                                checkVideoItem = videoItemList['items'][listIndex]
                                checkVideoId = None
                                if 'resourceId' in checkVideoItem['snippet']:
                                    checkVideoId = checkVideoItem['snippet']['resourceId']['videoId']
                                elif 'id' in checkVideoItem:
                                    checkVideoId = checkVideoItem['id']['videoId']

                                if checkVideoId == id:
                                    entry = videoItemList['items'][listIndex]

                                    entry['duration'] = {
                                        'seconds': durationInSeconds,
                                        'formatted': timeString
                                    }
                                    # listCounter += 1

                        # search youtube
                        counter = -1
                        videoIds = ""
                    counter += 1

        # print(videoItemList)
        return videoItemList
    def durationToHHMMSS(self, time):
        day = str(time // (24 * 3600))
        time = time % (24 * 3600)
        hour = time // 3600
        time %= 3600
        minutes = time // 60
        time %= 60
        seconds = time
        # print("d:h:m:s-> %d:%d:%d:%d" % (day, hour, minutes, seconds))

        if hour < 10:
            hour = "0" + str(hour)
        else:
            hour = str(hour)

        if minutes < 10:
            minutes = "0" + str(minutes)
        else:
            minutes = str(minutes)

        if seconds < 10:
            seconds = "0" + str(seconds)
        else:
            seconds = str(seconds)



        output = {
            'day':day,
            'hour':hour,
            'minute':minutes,
            'second':seconds
        }
        return output
    def formattedDurationToSeconds(self, formatted):
        split = formatted.split(':')
        secondsInhour = int(split[0])*60*60
        secondsInMinute = int(split[1])*60
        seconds = int(split[2])
        return secondsInhour+secondsInMinute+seconds
    def durationToSeconds(self, duration):
        """
        duration - ISO 8601 time format
        examples :
            'P1W2DT6H21M32S' - 1 week, 2 days, 6 hours, 21 mins, 32 secs,
            'PT7M15S' - 7 mins, 15 secs
        """
        split = duration.split('T')
        period = split[0]
        time = split[1]
        timeD = {}

        # days & weeks
        if len(period) > 1:
            timeD['days'] = int(period[-2:-1])
        if len(period) > 3:
            timeD['weeks'] = int(period[:-3].replace('P', ''))

        # hours, minutes & seconds
        if len(time.split('H')) > 1:
            timeD['hours'] = int(time.split('H')[0])
            time = time.split('H')[1]
        if len(time.split('M')) > 1:
            timeD['minutes'] = int(time.split('M')[0])
            time = time.split('M')[1]
        if len(time.split('S')) > 1:
            timeD['seconds'] = int(time.split('S')[0])

        # convert to seconds
        timeS = timeD.get('weeks', 0) * (7 * 24 * 60 * 60) + \
                timeD.get('days', 0) * (24 * 60 * 60) + \
                timeD.get('hours', 0) * (60 * 60) + \
                timeD.get('minutes', 0) * (60) + \
                timeD.get('seconds', 0)

        return timeS
    def GetDataFromFilename(self, file):
        base = os.path.basename(str(file))
        basepath = os.path.dirname(str(file))
        name, ext = os.path.splitext(base)

        splitName = name.split("@")
        internalId = splitName[0]
        internalVideoId = splitName[1]

        return {'basepath': basepath, 'filename': name, 'ext': ext, 'id' : {'internal': internalId, 'video': internalVideoId}}

    def printMessage(self, message):
        if DEBUG:
            print("[DEBUG]" + str(message))
    def sendProgressMessage(self, dataTransport, inputpayload, message):

        payload = self.create_payload(['row', 'playlist.playlist'])
        payload['id']['internal'] = inputpayload['id']['internal']
        payload['id']['video'] = inputpayload['id']['video']
        payload['row']['status'] = message

        dataTransport.put(self.createDataItem('server/result/video', payload))
    # string utils
    def unescape_string(self, x):
        list = {
            '\'': "\\\\u0027",
             '\"': "\\\\u0022",
            '\n': "\\\\u000D",
            # '&': "&amp;"

        }

        for key in list:
            x = x.replace(list[key], key)
        return x
    def escape_string(self,x):
        list = {
            '\'': "\\\\u0027",
            '\"': "\\\\u0022",
            '\n': "\\\\u000D",
            # '&': "&amp;"
                }

        for key in list:
            x = x.replace(key, list[key])
        return x
    # filter utils
    def escape_youtube_string(self,x):
        list = {
            '\'': "%",
            # '\"': "\\\\u0022",
            # '\n': "\\\\u000D",
            '&': "%26;"
        }

        for key in list:
            x = x.replace(key, list[key])
        return x
    def filter_string(self, x, list):

        # create a dictionary to have [searchable , replacewith]
        brackets = [["[", "]"], ["(", ")"], ["{", "}"], ["", ""]]
        # print(x)
        for item in list['items']:
            key = item['filter']['key']
            value = item['filter']['value']

            original = key
            lower = key.lower()
            upper = key.upper()
            firstLetterInWord = key.title()

            styles = [original, lower, upper, firstLetterInWord]


            for bracket in brackets:


                for keystyle in styles:
                    # print(bool(" " + bracket[0] + keystyle + bracket[1] in x))
                    # print(" " + bracket[0] + keystyle + bracket[1])
                    if (" " + bracket[0] + keystyle + bracket[1] + " ") in x:
                        # print(bool(" " + bracket[0] + key + bracket[1] + " " in x))
                        x = x.replace((" " + bracket[0] + keystyle + bracket[1] + " "), value + " ")

                    elif (" " + bracket[0] + keystyle + bracket[1]) in x:

                        x = x.replace((" " + bracket[0] + keystyle + bracket[1]), value)

                    elif (bracket[0] + keystyle + bracket[1] + " ") in x:
                        x = x.replace((bracket[0] + keystyle + bracket[1] + " "), value)

                    elif (bracket[0] + keystyle + bracket[1]) in x:

                        x = x.replace((bracket[0] + keystyle + bracket[1]), value)



            # x = x.replace(key, list[key])
        return x
    def filter_string_input(self, x, list):
        for key in list:
            x = x.replace(key, '')

        return x
    def create_filter_item(self, key , value):
        filterid = str(uuid.uuid4())
        payload = self.create_payload(['filter'])
        payload['id']['filter'] = filterid
        payload['filter']['key'] = key
        payload['filter']['value'] = value

        # payload = {
        #     'filterid': filterid,
        #     'key': key,
        #     'value': value
        # }
        return payload
    def hasFilterKey(self,key, data):

        for item in data:
            if item['filter']['key'] == key:
                return True


        return False