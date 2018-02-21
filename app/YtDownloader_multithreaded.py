from __future__ import print_function
from __future__ import unicode_literals
import youtube_dl
import json
import requests
import threading
import multiprocessing
from urllib import request
from urllib.parse import quote
from urllib.parse import unquote
from urllib.parse import urlparse
from urllib.parse import parse_qsl
from multiprocessing import JoinableQueue
from multiprocessing.context import Process
import tornado.websocket
from queue import Queue
import stat
from subprocess import Popen, PIPE
import os
from mutagen.easyid3 import EasyID3
import uuid
import re  # Regular expression library
import sqlite3
import musicbrainzngs
import sys
import time
import datetime
import random
import shutil
import xml.etree.ElementTree as etree
#MBHOST = "musicbrainz-mirror.eu:5000"
MBHOST = "fatso.diskstation.me:8086"
musicbrainzngs.set_hostname(MBHOST)
musicbrainzngs.set_useragent(
    "traxter",
    "0.2",
    "dimball@hotmail.com",
)
FFMPEG_CMD = ['ffmpeg']
EasyID3.RegisterTextKey('comment', 'COMM')
DEBUG = True



# global OUTPUTFOLDER
# global INCOMPLETEFOLDER
# global DBFILE
# global DBFILTER
# global DBSEARCH

g_filterlist = {
            '/': '_',

            "\"": '',
            '\'': '',
            '  ': ' ',
            # special characters
            # '.': '',
            '&': ' and ',
            '?': '',
            'Official Music Video': '',
            'Official Lyric Video': '',
            'HQ and Lyrics': '',
            'HQ and LYRICS': '',
            'with lyrics': '',
            'Video': '',
            'OFFICIAL VIDEO': '',
            'Official Video': '',
            'OFFICIAL MUSIC VIDEO': '',
            'Official Audio': '',
            'Official Audio - HD': '',
            'Original Version': '',
            'HQ': '',
            'Official': '',
            'Explicit Audio': '',
            'OFFICIAL AUDIO': '',
            'Legendado_Lyric': '',
            'lyric video':'',

            'Original Uncensored Version': '',
            'Video Version': '',
            'MV': '',
            'Uncensored': '',
            'Lyric Video': '',
            'Lyrics in Description': '',
            'HD Visualized': '',
            'DOWNLOAD FREE IN DESCRIZIONE':'',
            'Audio': ''
        }



class c_utility():
    # path utils
    def SetDevMode(self):
        production_main = '/code/app/ws_app.py'

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
    def create_payload(self, parts = ['title.video', 'title.playlist', 'thumbnail', 'download.video', 'download.playlist', 'playlist.playlist', 'playlist.video', 'row']):
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
                        'seconds': '',
                        'formatted': '',

                    },
                    'offset': {
                        'seconds': '',
                        'formatted': '',
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
                    'formatted': ''
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
            index = data['index'][payload['id']['internal']]

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


            # print(trackresult)
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
                        'formatted': timeString
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
        print("searching for:" + artist + " " + album)
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
                                videoIds += searchVid['id']['videoId'] + ","
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
                    if 'id' in searchVid:
                        videoIds += searchVid['id']['videoId'] + ","
                        if counter == 49:
                            videoDataResponse = self.searchTimeData(videoIds, apikey)

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
                            counter = 0
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


class Main(threading.Thread, tornado.websocket.WebSocketHandler, c_utility):
    db = None
    def __init__(self, data):
        threading.Thread.__init__(self)
        self.printMessage("Using musicbrainhost:" + MBHOST)

        self.params = {}
        self.params['folder'] = self.SetDevMode()
        self.params['ApiKey'] = "AIzaSyBEUIk5lgvxJAw00ugcBbZRgUEFQWIu3LQ"
        self.params['plexToken'] = "7R4zqZsjqbdixgHni9yH"
        self.params['plexTimer'] = 10
        self.params['plexrun'] = True
        self.params['plexURL'] = 'fatso.diskstation.me:32400'
        self.params['download_threads'] = 8
        self.params['trackdl_threads'] = 2
        self.params['compare_yt_videos'] = 10
        self.params['finish_threads'] = 2
        self.params['baseurl'] = "https://www.youtube.com/watch?v="
        self.params['data'] = data['structure']
        self.setDaemon(True)
        self.setName("Main")
        self.data = data['structure']
        self.data_filter = {
            'index':{},
            'items':[]
        }
        self.data_search = {
            'index': {},
            'items': []
        }
        self.params['filter'] = self.data_filter

        self.connections = data['connections']
        self.connection_id = data['connection_id']
        self.isRunning = True
        self.downloadWorkers = []
        self.converterWorkers = []
        self.trackworkers = []
        self.finishworkers = []
        self.plexworker = None
        self.convertResult = data['convert_result']
        self.DownloadQueue = Queue()
        self.videoQueue = Queue()
        self.finishQueue = Queue()
        self.plexQueue = Queue()
        self.ConvertQueue = JoinableQueue()
        self.dataTransport = data['data_transport']
        self.MessageQueue = data['MessageQueue']

        self.PlaylistQueue = data['playlist']
        self.PlaylistManager = PlayListManager(self, self.params)
        self.PlaylistManager.start()



    # database utils
    def create_table(self, conn, create_table_sql):
        """ create a table from the create_table_sql statement
        :param conn: Connection object
        :param create_table_sql: a CREATE TABLE statement
        :return:
        """
        try:
            c = conn.cursor()
            c.execute(create_table_sql)
        except sqlite3.Error as e:
            self.printMessage(str(e))
    def checkDB(self, db):
        if os.path.isfile(db):
            if os.path.getsize(db) > 100:
                with open(db, 'r', encoding="ISO-8859-1") as f:
                    header = f.read(100)
                    if header.startswith('SQLite format 3'):
                        self.printMessage("SQLite3 database has been detected.")
                        return True
                    else:
                        return False
            else:
                return False
        else:
            return False
    def connectDB(self, db):
        bIsNewDB = False
        if not os.path.isfile(db):
            bIsNewDB = True

        connection = sqlite3.connect(db)
        if bIsNewDB:
            self.printMessage("Creating tables")
            if db == self.params['folder']['dbfile']:
                self.create_table(connection, '''
                                            CREATE TABLE playlist( \
                                            internalId TEXT PRIMARY KEY,\
                                            data TEXT
                                            )
                                        ''')
                connection.commit()
            elif db == self.params['folder']['dbsearch']:
                self.create_table(connection, '''
                                            CREATE TABLE search( \
                                            searchTerm TEXT PRIMARY KEY,\
                                            data TEXT
                                            )
                                            ''')
                connection.commit()

                self.create_table(connection, '''
                                            CREATE TABLE mbsearch_tracks( \
                                            id TEXT PRIMARY KEY,\
                                            data TEXT
                                            )
                                            ''')
                connection.commit()
                self.create_table(connection, '''
                                            CREATE TABLE mbsearch_album( \
                                            searchTerm TEXT PRIMARY KEY,\
                                            data TEXT
                                            )
                                            ''')
                connection.commit()
            elif db == self.params['folder']['dbfilter']:
                self.create_table(connection, '''
                                            CREATE TABLE filter( \
                                            filterid TEXT PRIMARY KEY,\
                                            data TEXT
                                            )
                                            ''')

                connection.commit()
                self.db_filter = connection
                for key in g_filterlist:
                    item = self.create_filter_item(key, g_filterlist[key])
                    self.insert_data(quote(item['id']['filter']), item, "filter")

        return connection
    def insert_data(self, indexId, data, table, cursor=None):
        key = ''
        connection = None
        if table == 'playlist':
            key = 'internalId'
            connection = self.db
        elif table == 'search':
            key = 'searchTerm'
            connection = self.db_search
            if cursor != None:
                connection = cursor
        elif table == 'mbsearch_artist':
            key = 'searchTerm'
            connection = self.db_search
        elif table == 'mbsearch_album':
            key = 'searchTerm'

            connection = self.db_search
        elif table == 'mbsearch_tracks':
            key = 'id'
            connection = self.db_search
            if cursor != None:
                connection = cursor

        elif table == 'filter':
            key = 'filterid'
            connection = self.db_filter


        if len(self.select_by_id(connection, indexId, table, key)) == 0:

            cursor = connection.cursor()
            cursor.execute('''INSERT INTO ''' + table + '''
                              VALUES(?,?)''', (indexId, json.dumps(data)))
            self.printMessage("Adding ID:%s" % indexId)
            cursor.close()
            connection.commit()
        else:
            #update instead
            self.printMessage("Updating ID:%s" % indexId)
            self.update_table(connection, indexId, data, table, key)
    def update_table(self, conn, indexId, data, table, key, ):
        """
        update priority, begin_date, and end date of a task
        :param conn:
        :param id:
        :param data:
        """
        sql = ''' UPDATE ''' + table + '''
                  SET data = ?
                  WHERE ''' + key + ''' = ?'''
        cur = conn.cursor()

        cur.execute(sql, (json.dumps(data), indexId, ))
        cur.close()
        conn.commit()
    def select_by_id(self, conn, indexId, table, key):
        """
        Query tasks by priority
        :param conn: the Connection object
        :param internalId:
        :return:
        """
        cur = conn.cursor()
        # print("table:%s key:%s value:%s", table, key, indexId)
        cur.execute("SELECT * FROM " + table + " WHERE " + key + "=?", (indexId,))
        # print("%s %s", key,indexId)
        rows = cur.fetchall()
        # print(rows)
        cur.close()
        return rows
    def select_all_from_table(self, conn, table):

        cur = conn.cursor()
        cur.execute("SELECT * FROM " + table)

        rows = cur.fetchall()
        cur.close()
        return rows
    def delete_from_table(self, conn,id, key, table):
        cur = conn.cursor()
        query = "delete from " + table + " where " + key + " = '%s' " % id
        # print(query)
        cur.execute(query)
        conn.commit()
        cur.close()
    def readData(self, conn, inputData, table):
        data = self.select_all_from_table(conn, table)
        counter = 0
        for row in data:
            jsonData = json.loads(row[1])
            inputData['items'].append(jsonData)
            inputData['index'][row[0]] = counter
            counter += 1
    def updateAllTitles(self, titletype):
        rows = []
        for entry in self.data['items']:
            for row in entry['items']:
                if row['row']['modified'] == False:

                    if entry['playlist']['type'] == 'playlist':
                        originalTitle = row['title']['video'][titletype]
                        title = self.filter_string_input(originalTitle,
                                                         [(row['row']['tracknumber'] + " - "),
                                                          entry['title']['playlist']['artist'] + " - "])
                        row['title']['video']['track'] = self.escape_string(self.filter_string(title, self.data_filter))

                    rowEntry = self.create_payload(['title.video'])
                    rowEntry['id']['internal'] = entry['id']['internal']
                    rowEntry['id']['video'] = row['id']['video']
                    rowEntry['title']['video']['track'] = row['title']['video']['track']

                    rows.append(rowEntry)

            if entry['playlist']['type'] == 'playlist':
                self.insert_data(entry['id']['internal'], entry, "playlist")

        return rows
    def removeItem(self, id, idName, data):
        index = data['index'][id]
        del data['items'][index]
        del data['index'][id]
        # reindex the index data
        counter = 0
        for item in data['items']:
            data['index'][item['id'][idName]] = counter
            counter+=1
    # search utils
    def searchYoutube(self, search_string, maxresults=49):
        # print(self.params['ApiKey'])
        searchFields = "items(id(videoId),snippet(title, thumbnails, description))"
        searchAPIurl = "https://www.googleapis.com/youtube/v3/search?part=snippet&fields=" + searchFields + "&q=" + \
                       quote(search_string) + "&maxResults=" + str(maxresults) + "&key=" + self.params['ApiKey']
        SearchResponse = requests.get(searchAPIurl)
        SearchResponse = json.loads(SearchResponse.text)
        if 'error' in SearchResponse:
            print('Error in response!!')
            # print(SearchResponse)
            SearchResponse['items'] = []
            return SearchResponse
        else:
            SearchResponse = self.InsertTimeData(SearchResponse, self.params['ApiKey'])
            return SearchResponse
    def getMbTrackResults(self, payload, cursor=None):
        dbcursor = self.db_search
        if cursor != None:
            dbcursor = cursor

        search_results = self.select_by_id(dbcursor, payload['musicbrainz']['id'], 'mbsearch_tracks', 'id')
        # print("number of track results:" + str(len(search_results)))
        if len(search_results) == 0:
            self.printMessage("searching on musizbrainz for tracks")
            try:
                search_results = self.get_tracks(payload['musicbrainz']['id'])
                if search_results != None:
                    # returns an array
                    # store the search results in the database
                    self.insert_data(payload['musicbrainz']['id'], search_results, 'mbsearch_tracks', dbcursor)
                    return search_results
                else:
                    return None
            except requests.exceptions.ConnectionError as e:
                self.printMessage("Could not connect to internet")

        else:
            self.printMessage("using cached search")
            # payload['results']['data'] = json.loads(search_results[0][1])
            return json.loads(search_results[0][1])
    def getYoutubeResults(self, payload, cursor=None):
            dbcursor = self.db_search
            if cursor != None:
                dbcursor = cursor

            search_results = self.select_by_id(dbcursor, quote(payload['results']['searchterm']), 'search', 'searchTerm')
            # print("number of results:" + str(len(search_results)))
            if len(search_results) == 0:
                self.printMessage("searching on youtube for videos")
                try:
                    search_results = self.searchYoutube(payload['results']['searchterm'])
                    # store the search results in the database

                    # if the search term has changed then get new, if not use the stored one
                    payload['results']['data'] = []
                    dataInsertItem = self.getdata('playlist', self.data, payload)
                    playlistType = dataInsertItem['playlist']['type']
                    # dataMessage = {"items": []}
                    counter = 0
                    for searchVid in search_results['items']:
                        if 'id' in searchVid:
                            videoPayload = self.create_payload(
                                ['playlist.playlist', 'download.video', 'results', 'thumbnail', 'row', 'title.video', 'custom'])
                            videoPayload['id']['internal'] = payload['id']['internal']
                            videoPayload['id']['video'] = payload['id']['video']
                            videoPayload['download']['current']['videoId'] = searchVid['id']['videoId']
                            videoPayload['results']['description'] = searchVid['snippet']['description']
                            videoPayload['thumbnail']['current']['default'] = \
                            searchVid['snippet']['thumbnails']['default'][
                                'url']
                            videoPayload['thumbnail']['current']['large'] = \
                                searchVid['snippet']['thumbnails']['high'][
                                    'url']
                            videoPayload['results']['index'] = counter
                            videoPayload['row']['tracknumber'] = payload['row']['tracknumber']
                            videoPayload['title']['video']['youtube'] = searchVid['snippet']['title']
                            videoPayload['playlist']['type'] = playlistType
                            videoPayload['custom']['isoriginal'] = False

                            if 'duration' in searchVid:
                                videoPayload['results']['duration']['seconds'] = searchVid['duration']['seconds']
                                videoPayload['results']['duration']['formatted'] = searchVid['duration']['formatted']

                            payload['results']['data'].append(videoPayload)
                            counter += 1

                    if len(payload['results']['data'])>0:
                        self.insert_data(quote(payload['results']['searchterm']), payload['results']['data'], 'search', dbcursor)
                    # self.dataTransport.put(self.createDataItem('server/store/results', payload))

                    # time.sleep(2)

                    # print("number of rows in payload data" + str(len(payload['results']['data'])))
                        if len(payload['results']['itemrange']) == 2:
                            # print("Cropping data")
                            dataInRange = []
                            if payload['results']['itemrange'][1] > len(payload['results']['data']):
                                payload['results']['itemrange'][1] = len(payload['results']['data'])

                            for i in range(payload['results']['itemrange'][0], payload['results']['itemrange'][1]):
                                dataInRange.append(payload['results']['data'][i])

                            payload['results']['data'] = dataInRange

                    # print("returning youtube data:")
                    # print(payload['results']['data'])
                    return payload
                except requests.exceptions.ConnectionError as e:
                    self.printMessage("Could not connect to internet")

            else:
                self.printMessage("using cached search")
                # print(search_results[0][1])
                # print("internal id:" + payload['id']['internal'])
                payload['results']['data'] = json.loads(search_results[0][1])
                # print(len(payload['results']['data']))

                if len(payload['results']['itemrange']) == 2:
                    # print("start:" + str(payload['results']['itemrange'][0]))
                    # print("end:" + str(payload['results']['itemrange'][1]))
                    dataInRange = []
                    if payload['results']['itemrange'][1] > len(payload['results']['data']):
                        payload['results']['itemrange'][1] = len(payload['results']['data'])

                    for i in range(payload['results']['itemrange'][0], payload['results']['itemrange'][1]):
                        # print("getting data index:" + str(payload['results']['data'][i]['results']['index']))
                        payload['results']['data'][i]['id']['internal'] = payload['id']['internal']
                        payload['results']['data'][i]['id']['video'] = payload['id']['video']
                        dataInRange.append(payload['results']['data'][i])

                    payload['results']['data'] = dataInRange
                return payload

    # communication
    def updateClients(self, payload, targetClientID=None, bInvert=False):
        # this now puts a message on the message queue that goes into the main server thread.
        options = {
            'targetClientID' : targetClientID,
            'bInvert': bInvert
        }
        self.MessageQueue.put(self.createDataItem(options, payload))
    # queue utils
    def addPlaylistUrl(self, item):
        self.PlaylistQueue.put(item)
    def stop(self):
        for p in multiprocessing.active_children():
            p.terminate()
        for p in self.downloadWorkers:
            p.stop()
        for p in self.finishworkers:
            p.stop()

        self.plexworker.stop()
        self.PlaylistManager.stop()
        self.dataTransport.put('STOP')
        self.isRunning = False

    def run(self):


        self.db = self.connectDB(self.params['folder']['dbfile'])
        self.readData(self.db, self.data, "playlist")

        self.db_filter = self.connectDB(self.params['folder']['dbfilter'])
        self.readData(self.db_filter, self.data_filter, "filter")
        self.db_search = self.connectDB(self.params['folder']['dbsearch'])
        self.readData(self.db_search, self.data_search, "search")

        self.plexworker = plexupdater(self, self.params)
        self.plexworker.start()
        for i in range(int(self.params['download_threads'])):
            dlworker = DownloadWorker(self, i)
            dlworker.start()
            self.downloadWorkers.append(dlworker)

        for i in range(int(self.params['trackdl_threads'])):
            trackdlworker = trackworker(self, self.params)
            trackdlworker.start()
            self.trackworkers.append(trackdlworker)

        for i in range(int(self.params['finish_threads'])):
            finishworker = finisher(self, self.params)
            finishworker.start()
            self.finishworkers.append(finishworker)

        for i in range(multiprocessing.cpu_count()):
            converterItem = ConverterWorker(self, i)
            converterItem.start()
            self.converterWorkers.append(converterItem)



        while self.isRunning:
            # print("Thread is running:%s" % self.getName())
            # this thread assembles the data structure depending on the type
            try:
                dataItem = self.dataTransport.get()
                if dataItem is 'STOP':
                    break
                if not self.isRunning:
                    break


                if dataItem['type'] == 'server/add/playlist':
                    payload = dataItem['payload']
                    self.setdata('playlist', self.data, payload)
                    dataInsertItem = self.getdata('playlist', self.data, payload)
                    self.insert_data(payload['id']['internal'], dataInsertItem, "playlist")
                #     update all connected clients

                    self.updateClients(self.createDataItem('client/add/playlist', payload))
                elif dataItem['type'] == 'server/add/url':
                    payload = dataItem['payload']
                    self.PlaylistQueue.put(payload)

                elif dataItem['type'] == 'server/get/playlists':

                    payload = dataItem['payload']
                #   update all client

                    for item in self.data['items']:
                        payload['items'].append(item)

                    removeList = []
                    # print(payload['custom'])
                    if 'filter_playlist' in payload['custom']:
                        # print("ejje")
                        for item in payload['items']:
                            # print(item['playlist']['type'])
                            if item['playlist']['type'] == 'playlist':
                                # print("adding to list")
                                removeList.append(item)
                    if 'filter_artistalbum' in payload['custom']:
                        for item in payload['items']:
                            if item['playlist']['type'] == 'artistalbum':
                                removeList.append(item)

                    # print(len(removeList))
                    for rem in removeList:
                        payload['items'].remove(rem)
                        # print("removing:" + rem['title']['playlist']['artist'])

                    # for item in payload['items']:
                        # print(item['playlist']['type'])
                    if 'client' in payload['id']:
                        self.updateClients(self.createDataItem('client/set/playlists', payload), payload['id']['client'], False)
                    else:
                        self.printMessage("Cannot send to client. Sending to all")
                        print(payload)
                        self.updateClients(self.createDataItem('client/set/playlists', payload))

                elif dataItem['type'] == 'server/add/video':
                    payload = dataItem['payload']
                    self.setdata('video', self.data, payload)
                    dataInsertItem = self.getdata('playlist', self.data, payload)
                    self.insert_data(payload['id']['internal'], dataInsertItem, "playlist")
                    # self.updateClients(dataItem)
                elif dataItem['type'] == 'server/add/recording':
                    payload = dataItem['payload']
                    self.setdata('video', self.data, payload)
                    dataInsertItem = self.getdata('playlist', self.data, payload)
                    self.insert_data(payload['id']['internal'], dataInsertItem, "playlist")
                    # self.updateClients(dataItem)
                elif dataItem['type'] == 'server/get/videos':
                    self.printMessage("Getting videos")
                    payload = dataItem['payload']
                    playlistItem = self.getdata('playlist', self.data, payload)
                    clientid = dataItem['payload']['id']['client']
                    # print(playlistItem['items'])

                    self.updateClients(self.createDataItem('client/add/multiplevideos', playlistItem), clientid)
                elif dataItem['type'] == 'server/result/video':
                    payload = dataItem['payload']
                    playlistItem = self.getdata('playlist', self.data, payload)
                    if payload['id']['video'] in playlistItem['index']:
                        index = playlistItem['index'][payload['id']['video']]
                        videoDataItem = playlistItem['items'][index]
                    else:
                        videoDataItem = playlistItem['playlist']['videoItem']

                    videoDataItem['row']['status'] = payload['row']['status']
                    numCompleted = 0

                    totalItems = 0
                    for track in playlistItem['items']:
                        if track['row']['selected']:
                            totalItems += 1

                    totalItems = totalItems*4

                    for videoItem in playlistItem['items']:
                        if 'downloading' in videoItem['row']['status']:
                            numCompleted += 1
                        if 'waiting to convert' in videoItem['row']['status']:
                            numCompleted += 2
                        if 'converting' in videoItem['row']['status']:
                            numCompleted += 3
                        elif 'complete' in videoItem['row']['status']:
                            numCompleted += 4
                        elif 'failed' in videoItem['row']['status']:
                            numCompleted += 4

                    playlistItem['playlist']['progress'] = numCompleted/totalItems*100
                    payload['playlist']['progress'] = numCompleted/totalItems*100

                    self.insert_data(payload['id']['internal'], playlistItem, "playlist")


                    if playlistItem['playlist']['progress'] == 100.0:
                    #     send the job to the finish worker thread
                        self.finishQueue.put(playlistItem)

                    # if the download has completed at 100% then start moving from the temporary download directory to
                    #   the final output directory
                    #     go through each videoDataItem and move the file to the correct folder





                    self.updateClients(self.createDataItem('client/result/video', payload))









                elif dataItem['type'] == 'server/result/import':
                    payload = dataItem['payload']
                    playlistItem = self.getdata('playlist', self.data, payload)

                    playlistItem['playlist']['import_progress'] = payload['custom']['progress']
                    self.insert_data(payload['id']['internal'], playlistItem, "playlist")
                    self.updateClients(self.createDataItem('client/result/import', payload))

                elif dataItem['type'] == 'server/remove/playlist':
                    self.printMessage("Removing playlist:%s" % dataItem['payload']['id']['internal'])
                    try:
                        payload = dataItem['payload']
                        playlistItem = self.getdata('playlist', self.data, payload)
                        payload['items'] = playlistItem['items']
                        self.removedata('playlist', self.data, payload)
                        self.delete_from_table(self.db, payload['id']['internal'], 'internalid', 'playlist')
                        self.updateClients(self.createDataItem('client/remove/playlist', payload))
                    except KeyError as e:
                        print(str(e))
                        pass
                elif dataItem['type'] == 'server/remove/cache':
                    self.printMessage("Removing search cache")
                    # tables = ['search', 'mbsearch_tracks', '']

                    # try:
                    self.printMessage("Removing youtube search cache")
                    datatable = self.select_all_from_table(self.db_search, "search")
                    for data in datatable:
                        # print(data[0])
                        self.delete_from_table(self.db_search, quote(data[0]), 'searchTerm', 'search')
                    # except:
                    #     print("Could not delete youtube search cache")

                    try:
                        self.printMessage("Removing musicbrainz track cache")
                        datatable = self.select_all_from_table(self.db_search, "mbsearch_tracks")
                        for data in datatable:
                            self.delete_from_table(self.db_search, quote(data[0]), 'id', 'mbsearch_tracks')
                    except:
                        print("Could not delete musicbrainz track cache")

                    try:
                        self.printMessage("Removing musicbrainz album cache")
                        datatable = self.select_all_from_table(self.db_search, "mbsearch_album")
                        for data in datatable:
                            self.delete_from_table(self.db_search, quote(data[0]), 'searchTerm', 'mbsearch_album')
                    except:
                        print("Could not delete musicbrainz album cache")



                elif dataItem['type'] == 'server/remove/completedtasks':
                    self.printMessage("Removing completed tasks")
                    removeTasks = []
                    for item in self.data['items']:
                        if item['playlist']['progress'] == 100.0:
                            removeTasks.append(item['id']['internal'])

                    for id in removeTasks:
                        inputPayload = self.create_payload([])
                        inputPayload['id']['internal'] = id
                        self.removedata('playlist', self.data, inputPayload)
                        self.delete_from_table(self.db, id, 'internalid', 'playlist')

                    self.updateClients(self.createDataItem('client/set/playlists', self.data))



                elif dataItem['type'] == 'server/remove/alltasks':
                    self.printMessage("Removing all tasks")
                    for id in self.data['index']:
                        self.delete_from_table(self.db, id, 'internalid', 'playlist')

                    self.data['items'] = []
                    self.data['index'] = {}

                    self.updateClients(self.createDataItem('client/set/playlists', self.data))
                elif dataItem['type'] == 'server/process/playlist':
                    self.printMessage("starting download of playlist:%s" % dataItem['payload'])

                    # resetting the counters on clients
                    payload = dataItem['payload']
                    playlistItem = self.getdata('playlist', self.data, payload)
                    if payload['playlist']['type'] == 'playlist':
                        if payload['title']['playlist']['artist'] == '':
                            payload['title']['playlist']['artist'] = 'Various Artists'
                        if payload['title']['playlist']['album'] == '':
                            payload['title']['playlist']['artist'] = 'Mix'

                            playlistItem['title']['playlist']['artist'] = payload['title']['playlist']['artist']
                            playlistItem['title']['playlist']['album'] = payload['title']['playlist']['album']

                    for videoItem in playlistItem['items']:
                        if videoItem['row']['selected'] == False:
                            videoItem['row']['status'] = "skipped"
                        else:
                            videoItem['row']['status'] = "queued"

                    self.updateClients(self.createDataItem('client/reset/results', playlistItem['items']))
                    # time.sleep(2)
                    counter = 0
                    # for splitalbum mode it should only download a specified ID.

                    if playlistItem['playlist']['type'] == 'splitalbum':
                    #     download the playlist video id?

                        videoItem = playlistItem['playlist']['videoItem']
                        data = {
                            'playlistData': self.data,
                            'payload': videoItem,
                            'playlistItem': playlistItem
                        }

                        self.sendProgressMessage(self.dataTransport, videoItem, "downloading")
                        self.DownloadQueue.put(data)
                    else:
                        for videoItem in playlistItem['items']:
                            if videoItem['row']['selected']:
                                # if payload['playlist']['type'] == 'playlist':


                                time.sleep(0.4)
                                data = {
                                    'playlistData': self.data,
                                    'payload': videoItem
                                }

                                self.sendProgressMessage(self.dataTransport, videoItem, "downloading")



                                self.DownloadQueue.put(data)
                                counter += 1

                        playlistItem['playlist']['totalItems'] = counter
                elif dataItem['type'] == 'server/get/searchvideo':
                    #request a search on youtube for videos with the the title as search string

                    payload = dataItem['payload']

                    # do the search on youtube here!
                    dataMessage = self.getYoutubeResults(payload)
                    # print(len(dataMessage['results']['data']))
                    self.updateClients(self.createDataItem('client/set/searchvideo', dataMessage), payload['id']['client'],
                                           False)


                    #when done, send results back to the client that requested it
                elif dataItem['type'] == 'server/set/artist':
                    payload = dataItem['payload']
                    dataInsertItem = self.getdata('playlist', self.data, payload)
                    dataInsertItem['title']['playlist']['artist'] = self.escape_string(payload['title']['playlist']['artist'])
                    artist = dataInsertItem['title']['playlist']['artist']
                    album = dataInsertItem['title']['playlist']['album']

                    if artist == '' or artist == '-1':
                        artist = "Various Artists"
                    if album == '' or album == '-1':
                        album = "Mix"


                    artistalbum = artist + " - " + album

                    for videoItem in dataInsertItem['items']:
                        videoItem['download']['current']['ydl_opts']['outtmpl'] = self.params['folder']['incomplete'] + "/" + artist + "/" + artistalbum + "/" + dataInsertItem['id']['internal'] + \
                                                           "@" + videoItem['id']['video'] + '.%(ext)s'

                    self.insert_data(payload['id']['internal'], dataInsertItem, "playlist")

                    self.updateClients(self.createDataItem('client/set/artist', payload), payload['id']['client'], True)

                    rows = self.updateAllTitles('original')

                    dataMessage = self.create_payload(['custom'])
                    dataMessage['custom']['rows'] = rows

                    self.updateClients(self.createDataItem('client/update/rows', dataMessage))


                elif dataItem['type'] == 'server/set/newvideo':
                    payload = dataItem['payload']
                    dataInsertItem = self.getdata('playlist', self.data, payload)

                    if payload['playlist']['type'] == 'splitalbum':




                        if payload['download']['current']['videoId'] == dataInsertItem['playlist']['videoItem']['download']['original']['videoId']:
                            dataInsertItem['playlist']['videoItem']['title']['video']['youtube'] = ''
                            payload['title']['video']['original'] = dataInsertItem['playlist']['videoItem']['title']['video']['original']
                        else:
                            dataInsertItem['playlist']['videoItem']['title']['video']['youtube'] = self.escape_string(payload['title']['video']['youtube'])

                        dataInsertItem['playlist']['videoItem']['download']['current']['videoId'] = payload['download']['current']['videoId']
                        dataInsertItem['playlist']['videoItem']['download']['current']['url'] = self.params['baseurl'] + \
                                                                  payload['download']['current']['videoId']
                        dataInsertItem['playlist']['videoItem']['thumbnail']['current']['default'] = payload['thumbnail']['current']['default']
                        dataInsertItem['playlist']['videoItem']['row']['duration']['formatted'] = payload['row']['duration']['formatted']
                    else:

                        index = dataInsertItem['index'][payload['id']['video']]

                        videoData = dataInsertItem['items'][index]
                        if payload['download']['current']['videoId'] == videoData['download']['original']['videoId']:
                            videoData['title']['video']['youtube'] = ''
                            payload['title']['video']['original'] =  videoData['title']['video']['original']
                            payload['row']['modified'] = False
                            videoData['row']['modified'] = False

                        else:
                            videoData['title']['video']['youtube'] = self.escape_string(payload['title']['video']['youtube'])
                            videoData['row']['modified'] = True
                            payload['row']['modified'] = True

                        # payload['results']['duration'] = videoData['row']['duration']
                        if payload['results']['duration']['formatted'] != videoData['row']['duration']['formatted']:
                            payload['custom']['durationMatch'] = False
                        else:
                            payload['custom']['durationMatch'] = True

                        videoData['download']['current']['videoId'] = payload['download']['current']['videoId']
                        videoData['download']['current']['url'] = self.params['baseurl'] + payload['download']['current']['videoId']
                        videoData['thumbnail']['current']['default'] = payload['thumbnail']['current']['default']

                    self.insert_data(payload['id']['internal'], dataInsertItem, "playlist")

                    self.updateClients(self.createDataItem('client/set/newvideo', payload))
                elif dataItem['type'] == 'server/set/album':
                    payload = dataItem['payload']
                    dataInsertItem = self.getdata('playlist', self.data, payload)
                    dataInsertItem['title']['playlist']['album'] = self.escape_string(payload['title']['playlist']['album'])
                    artist = dataInsertItem['title']['playlist']['artist']
                    album = dataInsertItem['title']['playlist']['album']

                    if artist == '' or artist == "-1":
                        artist = "Various Artists"

                    if album == '' or album == '-1':
                        album = "Mix"

                    artistalbum = artist + " - " + album
                    # print(artistalbum)
                    for videoItem in dataInsertItem['items']:
                        videoItem['download']['current']['ydl_opts']['outtmpl'] = self.params['folder']['incomplete'] + "/" + artist + "/" + artistalbum + "/" + \
                                                           dataInsertItem['id']['internal'] + \
                                                           "@" + videoItem['id']['video'] + '.%(ext)s'

                    self.insert_data(payload['id']['internal'], dataInsertItem, "playlist")
                    rows = self.updateAllTitles('original')

                    self.updateClients(self.createDataItem('client/set/album', payload), payload['id']['client'], True)

                    dataMessage = self.create_payload(['custom'])
                    dataMessage['custom']['rows'] = rows

                    self.updateClients(self.createDataItem('client/update/rows', dataMessage))
                elif dataItem['type'] == 'server/set/tracktitle':
                    payload = dataItem['payload']
                    dataInsertItem = self.getdata('playlist', self.data, payload)
                    if dataInsertItem['playlist']['type'] == 'playlist':
                        index = dataInsertItem['index'][payload['id']['video']]
                        videoData = dataInsertItem['items'][index]
                        videoData['row']['modified'] = not payload['custom']['reset']

                        artist = self.getdata('playlist', self.data, payload)['title']['playlist']['artist']
                        original_title = videoData['title']['video']['original']

                        filtered_original_title = self.filter_string_input(original_title,
                                                                           [(payload['row']['tracknumber'] + " - "),
                                                                            artist + " - "])

                        if payload['title']['video']['track'] == filtered_original_title:
                            videoData['row']['modified'] = False

                        title = self.filter_string_input(payload['title']['video']['track'], [(payload['row']['tracknumber'] + " - "), artist + " - "])

                        videoData['title']['video']['track'] = self.escape_string(self.filter_string(title, self.data_filter))
                        self.insert_data(payload['id']['internal'], dataInsertItem, "playlist")

                        payload['title']['video']['track'] = videoData['title']['video']['track']
                        payload['row']['modified'] = videoData['row']['modified']

                    self.updateClients(self.createDataItem('client/set/tracktitle', payload))


                elif dataItem['type'] == 'server/get/filterlist':
                    payload = dataItem['payload']
                    self.updateClients(self.createDataItem('client/set/filterlist', self.data_filter), payload['id']['client'])
                # announce on all clients except the client it came from
                elif dataItem['type'] == 'server/add/filteritem':
                    payload = dataItem['payload']

                    if not payload['filter']['key'] in self.data_filter['index']:

                        dataInsertItem = self.create_filter_item(payload['filter']['key'], payload['filter']['value'])
                        self.data_filter['items'].append(dataInsertItem)
                        self.data_filter['index'][dataInsertItem['id']['filter']] = len(self.data_filter['items'])-1


                        rows = self.updateAllTitles('original')
                        dataMessage = self.create_payload(['filter', 'custom'])
                        dataMessage['id']['filter'] = dataInsertItem['id']['filter']
                        dataMessage['filter']['key'] = payload['filter']['key']
                        dataMessage['filter']['value'] = payload['filter']['value']
                        dataMessage['custom']['rows'] = rows

                        self.insert_data(quote(dataInsertItem['id']['filter']), dataInsertItem, "filter")
                        self.updateClients(self.createDataItem('client/add/filteritem', dataMessage))
                    else:
                        self.printMessage("Filter key already exists. Not adding")


                elif dataItem['type'] == 'server/set/filteritem':
                    payload = dataItem['payload']

                    # if not self.hasFilterKey(payload['filter']['key'], self.data_filter['items']):

                    index = self.data_filter['index'][payload['id']['filter']]
                    dataInsertItem = self.data_filter['items'][index]
                    dataInsertItem['filter']['key'] = payload['filter']['key']
                    dataInsertItem['filter']['value'] = payload['filter']['value']
                    rows = self.updateAllTitles('original')
                    self.insert_data(quote(dataInsertItem['id']['filter']), dataInsertItem, "filter")

                    self.updateClients(self.createDataItem('client/set/filteritem', payload), payload['id']['client'], True)
                    payload['custom'] = {
                        'rows': rows
                    }
                    self.updateClients(self.createDataItem('client/update/rows', payload))



                    # else:
                    #     index = self.data_filter['index'][payload['id']['filter']]
                    #     dataInsertItem = self.data_filter['items'][index]
                    #     rows = self.updateAllTitles('original')
                    #     payload['filter']['key'] = dataInsertItem['filter']['key']
                    #     payload['filter']['value'] = dataInsertItem['filter']['value']
                    #     self.insert_data(dataInsertItem['id']['filter'], dataInsertItem, "filter")
                    #
                    #     self.updateClients(self.createDataItem('client/set/filteritem', payload), payload['id']['client'], True)
                    #
                    #     payload['custom'] = {
                    #         'rows': rows
                    #     }
                    #     self.updateClients(self.createDataItem('client/update/rows', payload))
                    #     print("Filter key already exists. Not saving")


                elif dataItem['type'] == 'server/remove/filteritem':
                    payload = dataItem['payload']

                    self.removeItem(payload['id']['filter'], 'filter', self.data_filter)
                    rows = self.updateAllTitles('original')

                    # dataMessage = {
                    #     'filterid': payload['filterid'],
                    #     'rows': rows
                    # }
                    payload['custom'] = {
                        'rows': rows
                    }
                    self.delete_from_table(self.db_filter, payload['id']['filter'], 'filterid', "filter")
                    # self.insert_data(dataInsertItem['filterid'], dataInsertItem, "filter")
                    self.updateClients(self.createDataItem('client/remove/filteritem', payload))
                elif dataItem['type'] == 'server/set/selected':
                    payload = dataItem['payload']
                    dataInsertItem = self.getdata('playlist', self.data, payload)
                    index = dataInsertItem['index'][payload['id']['video']]
                    videoData = dataInsertItem['items'][index]
                    videoData['row']['selected'] = payload['row']['selected']
                    if payload['row']['selected']:
                        videoData['row']['status'] = 'queued'
                        payload['row']['status'] = 'queued'
                    else:
                        videoData['row']['status'] = 'skipped'
                        payload['row']['status'] = 'skipped'


                    self.insert_data(payload['id']['internal'], dataInsertItem, "playlist")
                    self.updateClients(self.createDataItem('client/set/selected', payload), payload['id']['client'], True)
                    self.updateClients(self.createDataItem('client/set/status', payload))
                elif dataItem['type'] == 'server/set/allselection':
                    payload = dataItem['payload']
                    dataInsertItem = self.getdata('playlist', self.data, payload)
                    dataArray = {'items':[]}
                    for videoData in dataInsertItem['items']:
                        dataPayload = self.create_payload(['row'])
                        videoData['row']['selected'] = payload['row']['selected']

                        dataPayload['id']['internal'] = dataInsertItem['id']['internal']
                        dataPayload['id']['video'] = videoData['id']['video']
                        dataPayload['row']['selected'] = payload['row']['selected']

                        if payload['row']['selected']:
                            videoData['row']['status'] = 'queued'
                            dataPayload['row']['status'] = 'queued'
                        else:
                            videoData['row']['status'] = 'skipped'
                            dataPayload['row']['status'] = 'skipped'

                        dataArray['items'].append(dataPayload)
                    self.insert_data(payload['id']['internal'], dataInsertItem, "playlist")
                    self.updateClients(self.createDataItem('client/set/allselected', payload), payload['id']['client'], True)
                    self.updateClients(self.createDataItem('client/set/allselection', dataArray))
                elif dataItem['type'] == 'server/get/mbalbums':
                    payload = dataItem['payload']

                    # check if search has already been done with this artist / album combination
                    searchterm = payload['results']['searchterm']['artist'] + "-" +  payload['results']['searchterm']['album']
                    self.printMessage("Performing musicbrainz search for " + searchterm)
                    search_results = self.select_by_id(self.db_search, quote(searchterm), 'mbsearch_album',
                                                       'searchTerm')
                    if len(search_results) == 0:
                        results = self.findArtistAlbum(payload['results']['searchterm']['artist'], payload['results']['searchterm']['album'])
                        if len(results) > 0:
                            # sort the results after release date
                            results.sort(key=lambda k: k['musicbrainz']['released']['seconds'], reverse=True)
                            # only store results if there are some results
                            self.insert_data(quote(searchterm), results, 'mbsearch_album')
                        else:
                            self.printMessage("No album results found")
                    else:
                        results = json.loads(search_results[0][1])

                    # print(results)
                    self.updateClients(self.createDataItem('client/set/mbalbums', results), payload['id']['client'], False)
                elif dataItem['type'] == 'server/update/splitalbum/duration':
                    payload = dataItem['payload']
                    dataInsertItem = self.getdata('playlist', self.data, payload)
                    dataInsertItem['playlist']['duration'] = payload['playlist']['duration']
                    self.insert_data(payload['id']['internal'], dataInsertItem, "playlist")
                    self.updateClients(self.createDataItem('client/update/splitalbum/duration', payload))
                elif dataItem['type'] == 'server/sort/videolist':
                    payload = dataItem['payload']
                    dataInsertItem = self.getdata('playlist', self.data, payload)
                    sortedList = []
                    offset = 0
                    for i in range(len(payload['custom'])):
                        position = payload['custom'][i]
                        position = position.split('_')[1]
                        index = dataInsertItem['index'][position]
                        videoItem = dataInsertItem['items'][index]
                        videoItem['row']['offset']['seconds'] = offset
                        timeObj = self.durationToHHMMSS(videoItem['row']['offset']['seconds'])
                        timeString = timeObj['hour'] + ":" + timeObj['minute'] + ":" + timeObj['second']
                        videoItem['row']['offset']['formatted'] = timeString
                        videoItem['row']['tracknumber'] = ("{0:02d}").format(i+1)
                        offset = offset + videoItem['row']['duration']['seconds']
                        sortedList.append(videoItem)
                        dataInsertItem['index'][position] = i
                        # print(videoItem['id']['video'] + " : " + videoItem['row']['tracknumber'] + " : " + videoItem['title']['video']['track'])

                    dataInsertItem['items'] = sortedList
                    self.insert_data(payload['id']['internal'], dataInsertItem, "playlist")
                    self.updateClients(self.createDataItem('client/update/sort/videolist', dataInsertItem))
                    self.updateClients(self.createDataItem('client/update/sort/videolist/full', dataInsertItem), payload['id']['client'], True)
                    # self.updateClients(self.createDataItem('client/add/multiplevideos', playlistItem), clientid)

                # elif dataItem['type'] == 'server/store/results':
                #     payload = dataItem['payload']
                #     print(payload)
                #     self.insert_data(payload['results']['searchterm'], payload['results']['data'], 'search')
                elif dataItem['type'] == 'server/set/splitalbum/track/duration':
                    payload = dataItem['payload']
                    dataInsertItem = self.getdata('playlist', self.data, payload)

                    index = dataInsertItem['index'][payload['id']['video']]
                    videoItem = dataInsertItem['items'][index]
                    videoItem['row']['duration']['formatted'] = payload['row']['duration']['formatted']
                    videoItem['row']['duration']['seconds'] = self.formattedDurationToSeconds(payload['row']['duration']['formatted'])

                    offset = 0
                    for i in range(len(dataInsertItem['items'])):
                        videoItem = dataInsertItem['items'][i]
                        videoItem['row']['offset']['seconds'] = offset
                        timeObj = self.durationToHHMMSS(videoItem['row']['offset']['seconds'])
                        timeString = timeObj['hour'] + ":" + timeObj['minute'] + ":" + timeObj['second']
                        videoItem['row']['offset']['formatted'] = timeString
                        offset = offset + videoItem['row']['duration']['seconds']

                    timeObj = self.durationToHHMMSS(offset)
                    timeString = timeObj['hour'] + ":" + timeObj['minute'] + ":" + timeObj['second']
                    dataInsertItem['playlist']['duration']['formatted'] = timeString
                    dataInsertItem['playlist']['duration']['seconds'] = offset
                    self.insert_data(payload['id']['internal'], dataInsertItem, "playlist")
                    self.updateClients(self.createDataItem('client/update/sort/videolist', dataInsertItem))
                # elif dataItem['type'] == 'server/set/splitalbum/track/offset':
                #     payload = dataItem['payload']
                #     dataInsertItem = self.getdata('playlist', self.data, payload)
                #
                #     index = dataInsertItem['index'][payload['id']['video']]
                #     videoItem = dataInsertItem['items'][index]
                #     videoItem['row']['offset']['formatted'] = payload['row']['offset']['formatted']
                #     videoItem['row']['offset']['seconds'] = self.formattedDurationToSeconds(payload['row']['offset']['formatted'])
                #
                #     offset = 0
                #     for i in range(len(dataInsertItem['items'])):
                #         videoItem = dataInsertItem['items'][i]
                #         videoItem['row']['offset']['seconds'] = offset
                #         timeObj = self.durationToHHMMSS(videoItem['row']['offset']['seconds'])
                #         timeString = timeObj['hour'] + ":" + timeObj['minute'] + ":" + timeObj['second']
                #         videoItem['row']['offset']['formatted'] = timeString
                #         offset = offset + videoItem['row']['duration']['seconds']
                #
                #     self.insert_data(payload['id']['internal'], dataInsertItem, "playlist")
                #     self.updateClients(self.createDataItem('client/sort/videolist', dataInsertItem))


            except KeyboardInterrupt:
                break
        self.printMessage("Thread is exiting:%s" % self.getName())
        self.printMessage("closing databases")
        self.db.close()
        self.db_filter.close()
        self.db_search.close()


class plexupdater(threading.Thread, c_utility):
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


class finisher(threading.Thread, c_utility):
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

                self.finishQueue.task_done()
            except KeyboardInterrupt:
                break
        self.printMessage("Thread is exiting:%s" % self.getName())

class trackworker(threading.Thread, c_utility):
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
            print("No results from youtube...")
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
                    print('creating artist album data type')

                    tracklist = self.main.getMbTrackResults(
                        payload,
                        self.dbsearch
                    )
                    if tracklist != None:
                        for track in tracklist:
                            self.addTrackItem(
                                payload['id']['internal'],
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
                    print('creating split album data type')
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

class PlayListManager(threading.Thread, c_utility):
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
                            print("Could not connect to internet")

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

class DownloadWorker(threading.Thread, c_utility):
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
                }
                filedata = self.GetDataFromFilename(d['filename'])
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

                            if i == retries:
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
class ConverterWorker(Process, c_utility):
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

        command = FFMPEG_CMD + args
        # self.printMessage('Calling: ' + str(self.command))
        pipe = Popen(command, stderr=PIPE)
        pipe.stderr.read()
        pipe.terminate()
        self.printMessage("[" + self.name + "] Conversion complete")
    def run(self):
        self.printMessage("Process is running:%s" % self.name)
        while self.isRunning:
            try:
                data = self.convertQueue.get()
                if data is 'STOP':
                    break


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
                if os.path.exists(outputFileName):
                    os.remove(outputFileName)

                if playlistItem['playlist']['type'] == 'splitalbum':
                #     set the ffmpeg arguments to split the file using some time arguments

                    # fileData = self.GetDataFromFilename(str(file))
                    videoData = data['videoItem']


                    outputFileName = path + '/' + videoData['row']['tracknumber'] + '-' + videoData['title']['track'] + '.mp3'

                    starttime = time.strftime('%H:%M:%S', time.gmtime(videoData['row']['duration']['offset']['seconds']))
                    endtime = time.strftime('%H:%M:%S', time.gmtime(videoData['row']['duration']['offset']['seconds']+videoData['row']['duration']['seconds']))
                    ffmpeg_args = ['-i',
                                filename,
                                '-acodec',
                                'copy',
                                '-ss ' + starttime,
                                '-to ' + endtime,
                               outputFileName]

                    self.sendProgressMessage(self.main.dataTransport, self.GetDataFromFilename(outputFileName), "converting")
                    self.execute_ffmpeg(ffmpeg_args)

                    # self.set_id3(outputFileName, playlistData)
                # use the offset property
                # time.strftime('%H:%M:%S', time.gmtime(12345))
                else:

                    outputFileName = path + '/' + file + '.mp3'




                    ffmpeg_args = ['-i',
                                        filename,
                                        '-q:a',
                                        '0',
                                        '-map',
                                        'a',
                                        outputFileName]
                    self.sendProgressMessage(self.main.dataTransport, self.GetDataFromFilename(outputFileName), "converting")

                    self.execute_ffmpeg(ffmpeg_args)
                    # remove the old unconverted audio file
                    filedata = self.GetDataFromFilename(outputFileName)


                    if os.path.exists(filedata['basepath'] + "/" + filedata['filename'] + ".temp" + filedata['ext']):
                        os.remove(filedata['basepath'] + "/" + filename + ".temp" + filedata['ext'])
                    elif os.path.exists(filename):
                        os.remove(filename)

                    # set the permissions on the file
                    os.chmod(outputFileName,
                             stat.S_IWGRP | stat.S_IRGRP | stat.S_IRUSR | stat.S_IWUSR | stat.S_IROTH | stat.S_IWOTH)


                    self.set_id3(outputFileName, playlistData)

                self.convertQueue.task_done()

                    # time.sleep(0.1)
            except KeyboardInterrupt:
                break
        self.printMessage("Process is exiting:%s" % self.name)




