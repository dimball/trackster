class c_utility():
    def GetDataFromFilename(self, file):
        base = os.path.basename(str(file))
        basepath = os.path.dirname(str(file))
        name, ext = os.path.splitext(base)

        splitName = name.split("@")
        internalId = splitName[0]
        videoId = splitName[1]

        return {'basepath': basepath, 'filename': name, 'ext': ext, 'internalId': internalId, 'videoId': videoId}
    def printMessage(self, message):
        if DEBUG:
            print("[DEBUG]" + message)

    def sendProgressMessage(self, dataTransport, payload, message):

        messagePayload = {
            'internalId': payload['internalId'],
            'videoId': payload['videoId'],
            'status': message
        }
        dataTransport.put(self.createDataItem('result/video', messagePayload))

    def createDataItem(self, type, payload):
        data = {
            'type': type,
            'payload': payload
        }
        return data
    def unescape_string(self, x):
        list = {
            '\'': "\\\\u0027",
            '\"': "\\\\u0022",
            '\n': "\\\\u000D"

        }

        for key in list:
            x = x.replace(list[key], key)
        return x
    def escape_string(self,x):
        list = {
            '\'': "\\\\u0027",
            '\"': "\\\\u0022",
            '\n': "\\\\u000D"

                }

        for key in list:
            x = x.replace(key, list[key])
        return x
    def string_cleanup(self, x):

        # create a tuple to have [searchable , replacewith]
        list = {
            '/': '_',
            '.': '',
            # '-': '_',
            "\"": '',
            '&': 'and',
            ' [Official Music Video]': '',
            ' (Official Music Video)': '',
            ' [Official Lyric Video]': '',
            ' (Official Lyric Video)': '',

            '[HQ and Lyrics]': '',
            'HQ and LYRICS': '',
            '\'': '',
            '(with lyrics)': '',
            'with lyrics': '',
            '(Video)': '',
            ' [OFFICIAL VIDEO]': '',
            ' [Official Video]': '',
            ' (Official Video)': '',
            ' [OFFICIAL MUSIC VIDEO]': '',
            ' (OFFICIAL MUSIC VIDEO)': '',
            ' (Official Audio)': '',
            ' (Official Audio - HD)': '',
            ' (Original Version)': '',
            ' [HQ]': '',
            ' (HQ)': '',
            ' HQ': '',
            ' [Official]': '',
            ' (Explicit Audio)': '',
            ' (OFFICIAL AUDIO)': '',
            ' [Legendado_Lyric]': '',
            '  ': ' ',
            ' (Original Uncensored Version)': '',
            ' (Video Version)': '',
            ' (MV)': '',
            ' (Uncensored)': '',
            ' [Uncensored]': '',
            ' Uncensored': '',
            ' (Lyric Video)': '',
            ' (Lyrics in Description)': '',
            ' [Lyrics in Description]': '',
            ' (HD Visualized)': '',
            ' [HD Visualized]': '',
            '?': '',
            '(DOWNLOAD FREE IN DESCRIZIONE)':'',
            ' (Audio)': ''
        }

        for key in list:
            x = x.replace(key, list[key])
        return x

    def setdata(self, type, data, payload):
        if type == 'playlist':
            data['items'].append(payload)
            data['index'][payload['internalId']] = len(data['items'])-1
        elif type == 'video':
            playlistItem = self.getdata('playlist', data, payload)
            playlistItem['items'].append(payload)
            playlistItem['index'][payload['videoId']] = len(playlistItem['items'])-1
        # elif type == 'recording':
        #     print('adding recording')


    def getdata(self, type, data, payload):
        if type == 'playlist':
            index = data['index'][payload['internalId']]

            payload = data['items'][index]
            return payload
        elif type == 'video':
            playlistItem = self.getdata('playlist', data, payload)
            index = playlistItem['index'][payload['videoId']]
            payload = playlistItem['items'][index]
            return payload
        # elif type == 'recording':
        #
        #     payload = 'test'
        #     return payload
    def removedata(self, type, data, payload):
        if type == 'playlist':
            index = data['index'][payload['internalId']]
            del data['items'][index]
            del data['index'][payload['internalId']]
            # reindex the index property

            for i in range(len(data['items'])):
                id = data['items'][i]['internalId']
                data['index'][id] = i
    def findalbums(self, artist, album):
        result = musicbrainzngs.search_releases(artist=artist, release=album, limit=100)
        return result
    def findTracklist(self, id):
        time.sleep(random.uniform(0.1, 1.0))
        tracklist = musicbrainzngs.search_recordings(reid=id)
        return tracklist['recording-list']
