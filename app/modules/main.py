from __future__ import print_function
from __future__ import unicode_literals
import json
import requests
import threading
import multiprocessing
from urllib.parse import quote
from multiprocessing import JoinableQueue
import tornado.websocket
from queue import Queue
import os
from mutagen.easyid3 import EasyID3
import sqlite3
import musicbrainzngs
import time
from common.utility import Utility
from modules.workers.plexupdater import Worker as Plexupdater
from modules.workers.finisher import Worker as Finisher
from modules.workers.track import Worker as Track
from modules.managers.playlist import Manager as PlayListManager
from modules.workers.download import Worker as Download
from modules.workers.converter import Worker as Converter
DEBUG = True

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

class Main(threading.Thread, tornado.websocket.WebSocketHandler, Utility):
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
            self.printMessage('Error in response!!')
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
                # print(search_results)
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
                    # print("ID should be:" + payload['id']['internal'])
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

        self.plexworker = Plexupdater(self, self.params)
        self.plexworker.start()
        for i in range(int(self.params['download_threads'])):
            dlworker = Download(self, i)
            dlworker.start()
            self.downloadWorkers.append(dlworker)

        for i in range(int(self.params['trackdl_threads'])):
            trackdlworker = Track(self, self.params)
            trackdlworker.start()
            self.trackworkers.append(trackdlworker)

        for i in range(int(self.params['finish_threads'])):
            finishworker = Finisher(self, self.params)
            finishworker.start()
            self.finishworkers.append(finishworker)

        for i in range(multiprocessing.cpu_count()):
            converterItem = Converter(self, i)
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
                        # print(payload)
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
                        self.printMessage(str(e))
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
                    # self.printMessage("starting download of playlist:%s" % dataItem['payload'])

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
                                    'payload': videoItem,
                                    'playlistItem': playlistItem
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
                            # print("inside")
                            dataInsertItem['playlist']['videoItem']['title']['video']['youtube'] = ''
                            payload['title']['video']['original'] = dataInsertItem['playlist']['videoItem']['title']['video']['original']
                        else:
                            # print(payload['title']['video']['youtube'])
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
                        offset = offset + videoItem['row']['duration']['seconds'] + videoItem['row']['silence']['seconds']
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
                    payloadSeconds = self.formattedDurationToSeconds(payload['row']['duration']['formatted'])
                    bSilenceModified = False
                    if videoItem['row']['duration']['seconds'] != payloadSeconds:
                    #     user has changed the duration of the track
                    #     check how many seconds difference it is from the last entered value
                    #     print(videoItem['row']['duration']['seconds'])
                        # however calculate the second difference from the original value that was initially set.

                        secondDifference = int(videoItem['row']['duration']['original']['seconds'])-payloadSeconds

                  #   if the difference is greater than 0 then
                    #   add this difference to the silence seconds
                        if secondDifference>=0:
                            videoItem['row']['silence']['seconds'] = secondDifference
                            bSilenceModified = True


                    videoItem['row']['duration']['formatted'] = payload['row']['duration']['formatted']
                    videoItem['row']['duration']['seconds'] = self.formattedDurationToSeconds(payload['row']['duration']['formatted'])
                    if bSilenceModified == False:
                        videoItem['row']['silence']['seconds'] = payload['row']['silence']['seconds']

                    offset = 0
                    for i in range(len(dataInsertItem['items'])):
                        videoItem = dataInsertItem['items'][i]
                        videoItem['row']['offset']['seconds'] = offset
                        timeObj = self.durationToHHMMSS(videoItem['row']['offset']['seconds'])
                        timeString = timeObj['hour'] + ":" + timeObj['minute'] + ":" + timeObj['second']
                        videoItem['row']['offset']['formatted'] = timeString
                        offset = offset + videoItem['row']['duration']['seconds'] + videoItem['row']['silence']['seconds']

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







