var ws;
var g_data;
var g_clientid;
var g_waiting_to_show = {};

var g_filter_is_open = false;
var g_iStart = 0
var g_iEnd = 0
var g_connectingTimerObj = null
var g_dltype = 1;
//Utilities
function isNumeric(value) {
    return /^-{0,1}\d+$/.test(value);
}
function unescape_string(text)
{
//    console.log('before:' + text)
    var list = {
         "\\\\u0027": "\'",
         "\\\\u0022": "\"",
//         "&quot;":"\"",
         "\\\"": "\"",
        "&amp;":"&",
        "\\u000D": "\n"

    }
    for (var x in list)
    {
        text = text.replaceAll(x, list[x])
    }
//    console.log('after:' + text)
    return text
}
String.prototype.replaceAll = function(target, replacement) {
  return this.split(target).join(replacement);
};
function CreateData(type, payload)
{
    var data = new Object();
    data.type = type;
    data.payload = payload;
    var jsonString = JSON.stringify(data);
//    console.log("Sending:" + jsonString)
    return jsonString
}

function CreateDataItem(parts = ['filter', 'title.video', 'title.playlist', 'thumbnail', 'download.video', 'download.playlist', 'playlist.video', 'playlist.playlist', 'row', 'results'])
{

    var payload = new Object()
    payload.id = new Object()
    payload.id.internal = ''
    payload.id.video = ''
    payload.id.client = ''

    if (parts.includes('filter'))
    {
        payload.id.filter = ''
        payload.filter = new Object()
        payload.filter.key = ''
        payload.filter.value = ''
    }
    if (parts.includes('title.video'))
    {
        payload.title = new Object()
        payload.title.video = new Object()

        payload.title.video.track = ''
        payload.title.video.youtube = ''
        payload.title.video.original = ''
    }
    if (parts.includes('title.playlist'))
    {
        payload.title = new Object()
        payload.title.playlist = new Object()
        payload.title.playlist.artist = ''
        payload.title.playlist.album = ''
    }

    if (parts.includes('thumbnail'))
    {
        payload.thumbnail = new Object()
        payload.thumbnail.original = new Object()
        payload.thumbnail.original.default = ''
        payload.thumbnail.original.large = ''
        payload.thumbnail.current = new Object()
        payload.thumbnail.current.default = ''
        payload.thumbnail.current.large = ''
    }

    if (parts.includes('download.video'))
    {
        payload.download = new Object()
        payload.download.original = new Object()
        payload.download.current = new Object()

        payload.download.original.url = ''
        payload.download.original.ydl_opts = ''
        payload.download.original.videoId = ''

        payload.download.current.url = ''
        payload.download.current.ydl_opts = ''
        payload.download.current.videoId = ''

    }

    if (parts.includes('download.playlist'))
    {
        payload.download = new Object()
        payload.download.playlistId = ''

    }

    if (parts.includes('row'))
    {
        payload.row = new Object()
        payload.row.status = ''
        payload.row.selected = ''
        payload.row.modified = ''
        payload.row.tracknumber = ''
        payload.row.duration = new Object()
        payload.row.duration.seconds = ''
        payload.row.duration.formatted = ''
        payload.row.offset = new Object()
        payload.row.offset.seconds = ''
        payload.row.offset.formatted = ''
        payload.row.silence = new Object()
        payload.row.silence.seconds = ''
    }
    if (parts.includes('playlist.video'))
    {
        payload.playlist = new Object()
        payload.playlist.title = ''
    }

    if (parts.includes('playlist.playlist'))
    {
        payload.playlist = new Object()
        payload.playlist.progress = ''
        payload.playlist.import_progress = ''
        payload.playlist.totalItems = ''

        payload.playlist.type = ''
        payload.playlist.url = ''

        payload.playlist.duration = new Object()
        payload.playlist.duration.seconds = ''
        payload.playlist.duration.formatted = ''

    }
    if (parts.includes('results'))
    {
        payload.results = new Object()
        payload.results.description = ''
        payload.results.duration = new Object()
        payload.results.duration.seconds = ''
        payload.results.duration.formatted = ''
        payload.results.title = ''
        payload.results.index = ''
        payload.results.searchterm = ''
        payload.results.itemrange = []
        payload.results.target = ''
    }

    if (parts.includes('musicbrainz'))
    {
        payload.musicbrainz = new Object()
        payload.musicbrainz.extscore
        payload.musicbrainz.title = ''
        payload.musicbrainz.artist = ''
        payload.musicbrainz.released = new Object()
        payload.musicbrainz.released.date
        payload.musicbrainz.released.seconds
        payload.musicbrainz.id = ''
        payload.musicbrainz.disambiguation = ''
        payload.musicbrainz.trackcount = ''

        payload.musicbrainz.tracks = []
    }
    if (parts.includes('musicbrainz.track'))
    {
        payload.mbtrack = new Object()
        payload.mbtrack.title = ''
        payload.mbtrack.duration = new Object()
        payload.mbtrack.duration.seconds = ''
        payload.mbtrack.duration.formatted = ''
        payload.mbtrack.duration.offset = new Object()
        payload.mbtrack.duration.offset.seconds = ''
        payload.mbtrack.duration.offset.formatted = ''

    }
    if (parts.includes('custom'))
    {
        payload.custom = new Object()
    }
    if (parts.includes('filter'))
    {
        payload.filter = new Object()
        payload.filter.key = ''
        payload.filter.value = ''
    }
    return payload
}

function addPlaylist() {
//this data depends on the type

}
//function setData(data)
//{
////    everytime a new client connects it will get the data that is sent as a parameter from the backend
////    console.log(data)
//
//    g_data = JSON.parse(data)
//
//
//}
function getData()
{
//    everytime a new client connects it will get the data that is sent as a parameter from the backend
//    console.log(data)

//    g_data = JSON.parse(data)
//      console.log("getting playlists")
      var payload = CreateDataItem(['custom'])
      payload.id.client = g_clientid
      payload.items = []
      payload.index = new Object()
      ws.send(CreateData("server/get/playlists", payload))
}
function connectingTimer()
{
    try {
        getData();
        clearInterval(g_connectingTimerObj);
    }
    catch(err) {
        console.log("Trying to connect")
    }

}


function onLoad() {
    var hostname = window.location.hostname
// This connect the client to the server. It will then send the client ID at this point.
    ws = new WebSocket("ws://" + hostname + ":8080/websocket");
//    onload initiates the websocket connection with the webserver backend
//    sets up the onmessage callback.
    ws.onmessage = function(e) {
//        console.log("receiving data:")
//        console.log(e.data)
        serverHandler(e.data)
    };



//    it will use the data that has been sent from the backend to create the html structure
//there is no guarantee that the client id has arrived at this point.
//g_connectingTimerObj = setInterval(connectingTimer, 10)

//    GenerateEntries();

}
function testJSON(text){
    try{
        JSON.parse(text);
        return true;
    }
    catch (error){
        return false;
    }
}
function serverHandler(data)
{

    if (testJSON(data))
    {
        jsonData = JSON.parse(data)
        payload = jsonData['payload']


        if (jsonData.hasOwnProperty('type'))
        {

//            console.log(jsonData.type)
            switch(jsonData.type)
            {
                case "client/add/playlist":
                    CreateSinglePlaylistEntry(payload)
                break;
                case "client/add/video":
                    CreateSingleVideoEntry(payload.playlist.type, payload)
                break;
                case 'client/add/multiplevideos':
                    for (var i in payload.items)
                    {
//                        console.log(items[i])
                        CreateSingleVideoEntry(payload.playlist.type, payload.items[i])
                    }
                    if (payload.items.length > 0)
                    {
                        $("#item_" + payload.items[0].id.internal).collapse('show');
                    }
                    else
                    {
                        console.log("No items returned from the server")
                    }
                break;
                case "client/set/playlists":
//                    console.log(payload)
                    var artistalbum = 0
                    var playlisttype = 0
                    $("#queue").empty()
                    for (var element in payload.items)
                    {
                //        console.log(g_data.items[element])
                        CreateSinglePlaylistEntry(payload.items[element])
//                        console.log(payload.items[element])
                        switch (payload.items[element].playlist.type)
                        {
                            case 'playlist':
                                playlisttype++
                            break
                            case 'artistalbum':
                                artistalbum++
                            break
                        }



                    }
                    $("#statusbar_total").text(payload.items.length + " tasks in list")
                    $("#statusbar_artistalbum").text(artistalbum + " artist/album")
                    $("#statusbar_playlist").text(playlisttype + " youtube playlist")
//                    console.log(artistalbum)
//                    console.log(playlisttype)
                break;

                case "client/add/recording":
                    CreateSingleVideoEntry(payload.playlist.type, payload)
                break;
                case "client/result/video":
//                    updateProgressBar(payload)
                    updateResult(payload)
                break;
                case "client/remove/playlist":
                    RemovePlaylist(payload)
                break;
                case "client/reset/results":
                    ResetResults(payload)
                break;
                case "client/set/clientid":
                    g_clientid = payload
                    g_waiting_to_show[g_clientid] = false
                    console.log('Current client ID is:' + g_clientid)
                    getData()
                break;
                case "client/set/artist":
                    $('#' + payload.id.internal + " .entry_artist").val(payload.title.playlist.artist)
//                    console.log(payload)
//                    updateRows(payload)


                break
                case "client/set/album":
                    $('#' + payload.id.internal + " .entry_album").val(payload.title.playlist.album)
//                    updateRows(payload)
                break
                case "client/set/tracktitle":

                    $("#" + payload.id.internal + "_" + payload.id.video + " .input-group-addon.tracknumber").val(payload.row.tracknumber)
                    $("#" + payload.id.internal + "_" + payload.id.video + " .form-control.track").val(unescape_string(payload.title.video.track))
                    SetEditStatus(payload)
                break
                case "client/set/searchvideo":
//                    "#" + payload.id.internal + "_" + payload.id.video  + " .video_alternate_items"
                    $(payload.results.target).empty()
//                    console.log(payload.results.target)
//                    console.log(payload.results.data)
//                    console.log($("#altvideos").length)
                    for (var video in payload.results.data)
                    {
                        var VideoItem = payload.results.data[video]

//                        console.log(VideoItem)
                          console.log(payload.results.target)
                          CreateAlternateVideos(VideoItem, payload.results.target)
                    }


                break;
                case "client/set/newvideo":

                    if (payload.playlist.type == 'splitalbum')
                    {
                        $("#" + payload.id.internal + " .img-responsive.thumbnail").prop('src', payload.thumbnail.current.default)
                        $("#" + payload.id.internal + " .align-middle.fullfile").text(unescape_string(payload.title.video.youtube))
                        $("#" + payload.id.internal + " .text-right.endTime").text('[' + unescape_string(payload.row.duration.formatted) + ']')
                    }
                    else
                    {
                        if (payload.title.video.youtube == '')
                        {
                            $("#" + payload.id.internal + "_" + payload.id.video + " .form-control.video").val(unescape_string(payload.title.video.original))
                        }
                        else
                        {
                            $("#" + payload.id.internal + "_" + payload.id.video + " .form-control.video").val(unescape_string(payload.title.video.youtube))
                        }


    //                    console.log($("#" + payload.id.internal + "_" + payload.id.video + ".input-group-addon.duration").text())
    //                    console.log(payload.results.duration.formatted)
                        if (payload.custom.durationMatch == false)
                        {
                            $("#" + payload.id.internal + "_" + payload.id.video + " .input-group-addon.videoduration").removeClass("same")
                            $("#" + payload.id.internal + "_" + payload.id.video + " .input-group-addon.videoduration").addClass("different")
                            $("#" + payload.id.internal + "_" + payload.id.video + " .input-group-addon.videoduration.different").text(payload.results.duration.formatted)
                        }
                        else
                        {
                            $("#" + payload.id.internal + "_" + payload.id.video + " .input-group-addon.videoduration").removeClass("different")
                            $("#" + payload.id.internal + "_" + payload.id.video + " .input-group-addon.videoduration").addClass("same")
                            $("#" + payload.id.internal + "_" + payload.id.video + " .input-group-addon.videoduration.same").text(payload.results.duration.formatted)
                        }

                        $("#" + payload.id.internal + "_" + payload.id.video + " .img-responsive.thumbnail").prop('src', payload.thumbnail.current.default)

                        SetEditStatus(payload)
                    }
                break;
                case "client/set/filterlist":
                    if (g_filter_is_open)
                    {
                        var counter = 0
                        for (var item in payload.items)
                        {
                            AddFilterItem(payload.items[item])
                        }
                    }
                break;
                case "client/add/filteritem":
                    if (g_filter_is_open)
                    {
                        AddFilterItem(payload)

                    }
                    else
                    {
//                    open up the filter window
//                           $("#filter_list").trigger('show.bs.dropdown')
//                           $("#filter_list").addClass("btn-group dropup show")
//                           $("#filter_list").dropdown('toggle')
//
                    }
                    updateRows(payload)
                break;
                case "client/set/filteritem":
                    if (g_filter_is_open)
                    {
                        $("#"+ payload.id.filter + " .filterKey").val(payload.filter.key)
                        $("#"+ payload.id.filter + " .filterValue").val(payload.filter.value)
                    }
                    updateRows(payload)
                break;
                case "client/update/rows":
//                    console.log(payload)
                    updateRows(payload)
                break;

                case "client/remove/filteritem":
                    if (g_filter_is_open)
                    {
                        $("#"+ payload.id.filter).remove()
                    }
                    updateRows(payload)
                break;

                case "client/set/selected":
                    $("#" + payload.id.internal + "_" + payload.id.video  + " .checkbox.selected .sel").prop('checked', payload.row.selected)

                break;
                case "client/set/status":
                    $("#" + payload.id.internal + "_" + payload.id.video + " .form-control.text-sm-center.status").val(payload.row.status)
                break;

                case "client/set/allselection":
//                sets the skip checkbox for all items in the playlist
                    for (var item in payload.items)
                    {
                        entry = payload.items[item]
                        $("#" + entry.id.internal + "_" + entry.id.video  + " .checkbox.selected .sel").prop('checked', entry.row.selected)
                        $("#" + entry.id.internal + "_" + entry.id.video + " .form-control.text-sm-center.status").val(entry.row.status)
                    }
                break;
                case "client/set/allselected":
//                sets the master skip checkbox that is on the playlist
                    $("#" + payload.id.internal + " .checkbox.selectall .selall").prop('checked', payload.row.selected)
                break;
                case "client/set/mbalbums":
                    $("#mb_results").empty()

                    for (var index in payload)
                    {
                        CreateMBAlbumEntries(payload[index])
                    }
                    SetSpinner(false, "fa fa-search", "#mb_searchIcon")
                    $("#mb_search").collapse("show")
                break;
                case "client/result/import":
                    updateProgressBar(payload)
                break;
                case "client/set/statusbar":
                    updateStatusbar(payload)
                break
                case "client/update/splitalbum/duration":
                    console.log("Trying to set data " + payload.playlist.duration.formatted)
                    $("#" + payload.id.internal + " .text-right.startTime").text("["+ payload.playlist.duration.formatted + "]")
                break;
                case "client/update/sort/videolist":
                    console.log("updating videolist")
                    PartiallyUpdateVideoList(payload)
                break;
                case "client/update/sort/videolist/full":
                    console.log("FULL updating videolist")
                    FullUpdateVideoList(payload)
//                    PartiallyUpdateVideoList(payload)
                break;

            }
        }
    }
}
function FullUpdateVideoList(payload)
{
   if ($("#" + payload.id.internal + "_toggle").hasClass("fa-chevron-down"))
   {
        $("#item_" + payload.id.internal).empty()
        for (var i in payload.items)
        {
//                        console.log(items[i])
            CreateSingleVideoEntry(payload.playlist.type, payload.items[i])
        }


   }
}
function PartiallyUpdateVideoList(payload)
{
    if ($("#" + payload.id.internal + "_toggle").hasClass("fa-chevron-down"))
    {
        for (var i in payload.items)
            {
                row = payload.items[i]
//                console.log(payload.id.internal + "_" + row.id.video)
//                console.log($("#" + payload.id.internal + "_" + row.id.video  + " .form-control.duration.start").text())
                $("#" + payload.id.internal + "_" + row.id.video  + " .form-control.duration.start").val(row.row.offset.formatted)
                $("#" + payload.id.internal + "_" + row.id.video  + " .form-control.duration.end").val(row.row.duration.formatted + "|" + row.row.silence.seconds.toString())
                $("#" + payload.id.internal + "_" + row.id.video  + " .input-group-addon.tracknumber").text(row.row.tracknumber)

//                $("#" + payload.id.internal + "_" + row.id.video  + " .form-control.track").text(row.title.video.track)

            }
            $("#" + payload.id.internal + " .text-right.startTime").text("["+ payload.playlist.duration.formatted + "]")

    }

}

function updateProgressBar(payload)
{
   $("#" + payload.id.internal + " .progress-bar.progress-bar-striped.active.progressValue").width(parseFloat(payload.custom.progress).toFixed( 2 ).toString() + "%")

   if (parseFloat(payload.custom.progress).toFixed( 2 ).toString() == 100)
   {
        if (payload.custom.reset == true)
        {
            $("#" + payload.id.internal + " .progress-bar.progress-bar-striped.active.progressValue").width("0%")
            $("#" + payload.id.internal + " .fa.fa-play-circle.fa-2x.start").prop('disabled', false)
            $("#" + payload.id.internal + " .btn.btn-sm.toggle").prop('disabled', false)
            $("#" + payload.id.internal + " .fa.fa-trash-o.fa-2x.delete").prop('disabled', false)
            $("#" + payload.id.internal + " .entry_artist").prop('disabled', false)
            $("#" + payload.id.internal + " .entry_album").prop('disabled', false)
            SetSpinner(false, "fa fa-chevron-right", "#" + payload.id.internal + "_toggle")
        }
        else
        {
           $("#" + payload.id.internal + " .progress-bar.progress-bar-striped.active.progressValue").text(parseFloat(payload.custom.progress).toFixed( 2 ).toString() + "% download complete")
        }
   }
   else
   {
        $("#" + payload.id.internal + " .progress-bar.progress-bar-striped.active.progressValue").text(payload.custom.message + " " + parseFloat(payload.custom.progress).toFixed( 2 ).toString() + "%")
        $("#" + payload.id.internal + " .fa.fa-play-circle.fa-2x.start").prop('disabled', true)
        $("#" + payload.id.internal + " .btn.btn-sm.toggle").prop('disabled', true)
        $("#" + payload.id.internal + " .fa.fa-trash-o.fa-2x.delete").prop('disabled', true)
        $("#" + payload.id.internal + " .entry_artist").prop('disabled', true)
        $("#" + payload.id.internal + " .entry_album").prop('disabled', true)
        SetSpinner(true, "fa fa-chevron-right", "#" + payload.id.internal + "_toggle")
   }



}
function SetEditStatus(payload)
{
//    console.log(payload.row.modified)
    if (payload.row.modified == false)
    {
        if ($("#" + payload.id.internal + "_" + payload.id.video + " .userinfo_parent .userinfo").length > 0)
        {
            $("#" + payload.id.internal + "_" + payload.id.video + " .userinfo_parent .userinfo").remove()
        }
    }
    else if (payload.row.modified == true)
    {
        if ($("#" + payload.id.internal + "_" + payload.id.video + " .userinfo_parent .userinfo").length == 0)
        {
            createUserStatus($("#" + payload.id.internal + "_" + payload.id.video + " .userinfo_parent"))
        }
    }

}
function updateRows(data)
{
    if ($("#" + data.id.internal + "_toggle").hasClass("fa-chevron-down"))
    {
        for (var i in data.custom.rows)
        {
            row = data.custom.rows[i]
    //        console.log(row)
            $("#" + row.id.internal + "_" + row.id.video + " .track").val(unescape_string(row.title.video.track))
        }
    }

}
function updateResult(payload)
{

   $("#" + payload.id.internal + "_" + payload.id.video + " .form-control.text-sm-center.status").val(payload.row.status)
   $("#" + payload.id.internal + " .progress-bar.progress-bar-striped.active.progressValue").width(payload.playlist.progress + "%")
   $("#" + payload.id.internal + " .progress-bar.progress-bar-striped.active.progressValue").text(parseFloat(payload.playlist.progress).toFixed( 2 ).toString() + "% download complete")
   if (parseFloat(payload.playlist.progress).toFixed(2) == 100.0)
   {
        SetSpinner(false, "fa fa-play-circle", "#" + payload.id.internal + "_start")
   }
}
function ResetResults(data)
{
   var internalId = ""

   for (var index in data)
   {
        var entry = data[index]
        var status = $("#" + entry.id.internal + "_" + entry.id.video + " .form-control.text-sm-center.status").val()
        if (status != "skipped")
        {
            $("#" + entry.id.internal + "_" + entry.id.video + " .form-control.text-sm-center.status").val("queued")
        }


//        document.getElementById(data[item].internalId).getElementsByClassName(data[item].videoId)[0].getElementsByClassName("progress")[0]
//        FileStatus.innerHTML = data[item].status
//        internalId = data[item].internalId
   }

   $("#" + data[0].id.internal + " .progress-bar.progress-bar-striped.active.progressValue").width("0%")
   $("#" + data[0].id.internal + " .progress-bar.progress-bar-striped.active.progressValue").text("0% download complete")


//   document.getElementById(internalId).getElementsByClassName('playlist_progressbar')[0].value = 0
//   document.getElementById(internalId).getElementsByClassName('playlist_progressbarValue')[0].innerHTML = "0%"
//   document.getElementById(internalId).getElementsByClassName('startElement')[0].disabled = true
//   document.getElementById(internalId).getElementsByClassName('removeElement')[0].disabled = true





}
function AddFilterItem(data)
{
    var sHtml="";
    sHtml += " <div class=\"row\" id=\"" + data.id.filter + "\">";
    sHtml += "      <div class=\"col-sm-5\">";
    sHtml += "          <input type=\"text\" class=\"form-control filterKey\" placeholder=\"filter\" aria-label=\"filter\" value=\"\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Keyr\"/>";
    sHtml += "      </div>";
    sHtml += "      <div class=\"col-sm-5\">";
    sHtml += "          <input type=\"text\" class=\"form-control filterValue\" placeholder=\"replace with\" aria-label=\"filter Value\" value=\"\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Value\"/>";
    sHtml += "      </div>";
    sHtml += "      <div class=\"col-sm-2\">";
    sHtml += "          <button type=\"button\" class=\"fa fa-trash-o fa-2x remove\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Remove\"></button>";
    sHtml += "      </div>";
    sHtml += "</div>";
    $("#filter_list .filter_items").prepend(sHtml)


    $("#"+ data.id.filter + " .filterKey").val(unescape_string(data.filter.key))
    $("#"+ data.id.filter + " .filterValue").val(unescape_string(data.filter.value))

    $("#"+ data.id.filter + " .remove").on('click', function (e) {
        e.stopPropagation();
        console.log("remove this item:" + data.id.filter)
        var payload = CreateDataItem(['filter'])
        payload.id.internal = data.id.internal
        payload.id.filter = data.id.filter
        payload.filter.key = $("#"+ data.id.filter + " .filterKey").val()
        ws.send(CreateData("server/remove/filteritem", payload))
        console.log("sending remove data")
    });

     $("#"+ data.id.filter + " .filterKey").keyup(function (e) {

        var payload = CreateDataItem(['filter'])
        payload.id.filter = data.id.filter
        payload.id.client = g_clientid
        payload.filter.key = $(this).val()
        payload.filter.value =  $("#"+ data.id.filter + " .filterValue").val()
        ws.send(CreateData("server/set/filteritem", payload))

        if ( event.which == 13 ) {
             event.preventDefault();
        }
    });
     $("#"+ data.id.filter + " .filterValue").keyup(function (e) {

        var payload = CreateDataItem(['filter'])
        payload.id.filter = data.id.filter
        payload.filter.key = $("#"+ data.id.filter + " .filterKey").val()
        payload.filter.value = $(this).val()
        payload.id.client = g_clientid
        ws.send(CreateData("server/set/filteritem", payload))

        if ( event.which == 13 ) {
             event.preventDefault();
        }
    });




}
function createUserStatus(parent)
{
    var sHtml = ""
    sHtml += "                  <span class=\"input-group-addon userinfo\" style=\"height:50px\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"stats\">"
    sHtml += "                      <i class=\"fa fa-pencil fa-1x\" aria-hidden=\"true\"></i>";
    sHtml += "                  </span>";
    $(sHtml).prependTo(parent);
}
function RemovePlaylist(payload)
{
    console.log("Removing ID:" + payload.id.internal)

    if ($("#" + payload.id.internal) != null)
    {
        $("#" + payload.id.internal).remove()
    }
    for (var videoItem in payload.items)
    {
        if ($("#" + payload.id.internal + "_" + payload.items[videoItem].id.video) != null)
        {
             $("#" + payload.id.internal + "_" + payload.items[videoItem].id.video).remove()
        }
    }
}
function CreateMBAlbumEntries(data)
{
    sHtml = ""
    sHtml += "<div class=\"dropdown-item mbalbum\" href=\"#\">";
    sHtml += "  <div class=\"row fluid\">";
    sHtml += "      <div class=\"col-sm-2\">";
    sHtml += "          <p class=\"text-sm-left score\" style=\"width:100%\">";
    sHtml +=                data.musicbrainz.score + "%"
    sHtml += "          </p>";
    sHtml += "      </div>";
    sHtml += "      <div class=\"col-sm-3\">";
    sHtml += "          <p class=\"text-sm-left artist\" style=\"width:100%;word-wrap: break-word;\">";
    sHtml +=                data.musicbrainz.artist;
    sHtml += "          </p>";
    sHtml += "      </div>";
    sHtml += "      <div class=\"col-sm-3\">";
    sHtml += "          <p class=\"text-sm-left title\" style=\"width:100%;word-wrap: break-word;\">";
    sHtml +=                unescape_string(data.musicbrainz.title);
    sHtml += "          </p>";
    sHtml += "      </div>";
    sHtml += "      <div class=\"col-sm-2\">";
    sHtml += "          <p class=\"text-sm-left released\" style=\"width:100%\">";
    sHtml +=                data.musicbrainz.trackcount
    sHtml += "          </p>";
    sHtml += "      </div>";
    sHtml += "      <div class=\"col-sm-2\">";
    sHtml += "          <p class=\"text-sm-left released\" style=\"width:100%\">";
    sHtml +=                data.musicbrainz.released.date
    sHtml += "          </p>";
    sHtml += "      </div>";


    sHtml += "  </div>";
    sHtml += "</div>";
    $(sHtml).appendTo($("#mb_results"));

    $('#mb_results .dropdown-item.mbalbum').last().on('click', function(){
        var album = jQuery.trim($(this).find(" .title").text())
        var artist = jQuery.trim($(this).find(" .artist").text())
        console.log("sending:" + artist + " - " + album + " id:" + data.musicbrainz.id)

        var payload = CreateDataItem(['playlist.playlist', 'title.playlist', 'musicbrainz'])
        payload.title.playlist.artist = artist
        payload.title.playlist.album = album
        payload.musicbrainz.id = data.musicbrainz.id

        switch (g_dltype)
        {
            case 1:
                payload.playlist.type = 'artistalbum'
            break;
            case 2:
                payload.playlist.type = 'splitalbum'
            break;
        }
        console.log(payload.playlist.type)
        ws.send(CreateData("server/add/url", payload));



    });
}
function CreateAlternateVersions(data)
{
// this is for alternate version when using artist album

    sHtml += "<a class=\"dropdown-item item\" data-index-type=\"1\" href=\"#\">";
    sHtml += "  <div class=\"row fluid\" style=\"height:50px\">";
    sHtml += "      <div class=\"col-sm-3\">";
    sHtml += "          <p class=\"text-sm-left\" style=\"width:100%\">";
    sHtml += "              <strong>";
    sHtml += "                  Divide";
    sHtml += "              </strong>";
    sHtml += "          </p>";
    sHtml += "  </div>";
    sHtml += "  <div class=\"col-sm-3\">";
    sHtml += "      <p class=\"text-sm-left\" style=\"width:100%\">";
    sHtml += "          wembley edition";
    sHtml += "      </p>";
    sHtml += "  </div>";
    sHtml += "  <div class=\"col-sm-2\">";
    sHtml += "      <p class=\"text-sm-left\" style=\"width:100%\">";
    sHtml += "          2017";
    sHtml += "      </p>";
    sHtml += "  </div>";
    sHtml += "  <div class=\"col-sm-2\">";
    sHtml += "      <p class=\"text-sm-left\" style=\"width:100%\">";
    sHtml += "          17";
    sHtml += "      </p>";
    sHtml += "  </div>";
    sHtml += "  <div class=\"col-sm-2\">";
    sHtml += "      <img src=\"" + data.thumbnanil.current.url + "\" class=\"img-responsive\" alt=\"ed sheeran x\" style=\"height:50px\">";
    sHtml += "  </div>";
    sHtml += "  </div>";
    sHtml += "</a>";


}
function CreateAlternateVideos(data, target)
{

// this is for alternate videos per video item
    var sHtml="";
//    console.log(data.results.index)
    sHtml += "<a class=\"dropdown-item item\" data-index-type=\"" + data.results.index +"\" href=\"#\">"
    sHtml += "  <div class=\"row fluid\">\n"
    sHtml += "      <div class=\"col-sm-9 text-truncate\" style=\"height:100%\">"
    sHtml += "          <p class=\"text-sm-left\" style=\"width:100%\">"
    var thumbnail_size = ""
    if (target == '#' + data.id.internal + '_' + data.id.video + ' .current_alternate_video')
    {
        sHtml += "              <em>"
        sHtml +=                    unescape_string(data.title.video.youtube)
        sHtml += "              </em>"
        thumbnail_size = "style=\"height:30px\""
    }
    else
    {
        sHtml += "              <strong class=\"alttitle\">"
        sHtml +=                    unescape_string(data.title.video.youtube)
        sHtml += "              </strong>"
        sHtml += "          <blockquote>"
        sHtml += "              <p>"
        sHtml += "                  <small>"
        sHtml +=                        unescape_string(data.results.description)
        sHtml += "                  </small>"
        sHtml += "              </p>"
        sHtml += "          </blockquote>"
    }
    sHtml += "      </div>"
    sHtml += "      <div class=\"col-sm-3\">"
//    sHtml += "          <iframe class=\"img-responsive\" id=\"player_" + data.videoId +""\" width=\"100\" height=\"50\" src=\"http://www.youtube.com/embed/" + data.videoId + "?rel=0&wmode=Opaque&enablejsapi=1;showinfo=0;controls=0\" frameborder=\"0\" allowfullscreen></iframe>"
    sHtml += "          <img src=\"" + data.thumbnail.current.default + "\" " + thumbnail_size + " class=\"img-responsive\">"
    if (data.results.duration.formatted != '')
    {
        sHtml += "          <p>[" + data.results.duration.formatted + "]</p>"
    }
    sHtml += "      </div>"
    sHtml += "  </div>"
    sHtml += "</a>"
    console.log("target is:" + target)
    $(sHtml).appendTo($(target));
    console.log("Creating new data")
    $(target + " .dropdown-item.item[data-index-type=" + data.results.index + "]").on('click', function (e) {

        var payload = CreateDataItem(['playlist.playlist', 'title.video', 'download.video', 'thumbnail', 'custom', 'row', 'results', 'custom'])
        payload.id.internal = data.id.internal
        payload.id.video = data.id.video
        payload.id.client = g_clientid
        payload.playlist.type = data.playlist.type
        payload.row.duration.formatted = data.results.duration.formatted
        payload.title.video.youtube = unescape_string(data.title.video.youtube)
        payload.download.current.videoId = data.download.current.videoId
        payload.thumbnail.current.default = data.thumbnail.current.default
        payload.custom.isoriginal = data.custom.isoriginal
        payload.row.modified = true
        payload.results.duration = data.results.duration

        ws.send(CreateData("server/set/newvideo", payload))
        $(target + " .form-control.search").val(data.title.video.youtube)
    })
//    function onYouTubeIframeAPIReady() {
//    var videos = $$('iframe'), // the iframes elements
//         players = [], // an array where we stock each videos youtube instances class
//         playingID = null; // stock the current playing video
//    for (var i = 0; i < videos.length; i++) // for each iframes
//    {
//         var currentIframeID = videos[i].id; // we get the iframe ID
//         players[currentIframeID] = new YT.Player(currentIframeID); // we stock in the array the instance
//         // note, the key of each array element will be the iframe ID
//
//         videos[i].onmouseover = function(e) { // assigning a callback for this event
//             var currentHoveredElement = e.target;
//             if (playingID) // if a video is currently played
//             {
//                 players[playingID].pauseVideo();
//             }
//             players[currentHoveredElement.id].playVideo();
//             playingID = currentHoveredElement.id;
//         };
//    }
//
// }
// onYouTubeIframeAPIReady();





}
function CreateSinglePlaylistEntry(data)
{

    var albumClass = ""
    var iconClass = ""
    var hidden = ""
    switch(data.playlist.type)
    {
        case 'playlist':
//            albumClass = "col-sm-7 artist"
            iconClass = "fa fa-youtube fa-2x"
            hidden = "invisible";
        break;
        case 'splitalbum':
//            albumClass = "col-sm-4 artist"
            iconClass = "fa fa-sitemap fa-2x"
        break;
        case 'artistalbum':
            iconClass = "fa fa-music fa-2x"
        break;
    }

    g_waiting_to_show[data.id.internal] = false;


    var sHtml="";
    sHtml += "<div class=\"card-header\" role=\"tab\" id=\"" + data.id.internal +"\">";
    sHtml += "      <div class=\"row\">";
    sHtml += "          <div class=\"col-sm-2 toggler\">";
    sHtml += "              <button type=\"button\" class=\"btn btn-sm toggle\" data-toggle=\"collapse\" href=\"#item_"+ data.id.internal+"\" aria-expanded=\"false\" aria-controls=\"item_"+ data.id.internal +  "\">";
    sHtml += "                  <span id=\"" + data.id.internal + "_toggle\" class=\"fa fa-chevron-right fa-2x toggle\"></span>";
    sHtml += "              </button>";

    sHtml += "          <div class=\"btn-group\" role=\"group\">";
    sHtml += "              <button id=\"" + data.id.internal + "_start\" type=\"button\" class=\"fa fa-play-circle fa-2x start\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Start download\"></button>";
    sHtml += "              <button type=\"button\" class=\"fa fa-trash-o fa-2x delete\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Remove download task\"></button>";
    sHtml += "          </div>";
    sHtml += "      </div>";

    if (data.playlist.type == 'splitalbum')
    {
        sHtml += "      <div class=\"col-sm-8\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Album title\">";
//        sHtml += "          <div class=\"input-group\" style=\"height:40px\">";
//        sHtml += "              <input type=\"text\" class=\"form-control entry_artist\" placeholder=\"Various Artists\" aria-label=\"Various Artists\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Artist\">";
//        sHtml += "          </div>";
        sHtml += "          <div class=\"row\">";
        sHtml += "              <div class=\"col-xs-2\">";
        sHtml += "                 <img style=\"height:50px;\" src=\"https://www.smashingmagazine.com/wp-content/uploads/2015/06/10-dithering-opt.jpg\" class=\"img-responsive thumbnail\">";
        sHtml += "              </div>";
        sHtml += "              <div class=\"col-sm-10\" style=\"padding-left: 5px;\">";
                sHtml += "          <div class=\"row\">";
                sHtml += "              <div class=\"col-sm-8\">";
                    sHtml += "              <h4 class=\"align-middle\">";
                    sHtml +=                    unescape_string(data.title.playlist.artist) + " - " + unescape_string(data.title.playlist.album)
                    sHtml += "              </h4>";
                sHtml += "              </div>";
                sHtml += "              <div class=\"col-sm-4\">";
                sHtml += "                  <h6 class=\"text-right startTime\"\">";
                sHtml += "                      [--:--:--]"
                sHtml += "                  </h6>";
                sHtml += "              </div>";
                sHtml += "          </div>";
                sHtml += "          <div class=\"row\">";

                sHtml += "              <div class=\"col-sm-8\">";
                sHtml += "                  <h6 class=\"align-middle fullfile\"\">";
                sHtml += "Please select a full album from the list -->"
                sHtml += "                  </h6>";
                sHtml += "              </div>";
                sHtml += "              <div class=\"col-sm-4\">";
                sHtml += "                  <h6 class=\"text-right endTime\"\">";
                sHtml += "                      [--:--:--]"
                sHtml += "                  </h6>";
                sHtml += "              </div>";
                sHtml += "          </div>";
        sHtml += "              </div>";
        sHtml += "          </div>";


        sHtml += "      </div>";
//        sHtml += "      <div class=\"col-sm-5 album\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Artist name\">";
//        sHtml += "          <div class=\"input-group\">";
//        sHtml += "              <div class=\"input-group\" style=\"height:40px\">";
//        sHtml += "                 <input type=\"text\" class=\"form-control entry_album\" placeholder=\"Album\" aria-label=\"track\" value=\"\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Album\">";
//        sHtml += "              </div>";
//        sHtml += "          </div>";
//        sHtml += "      </div>";
    }
    else if (data.playlist.type == 'playlist')
    {
        sHtml += "      <div class=\"col-sm-4 album style\">";
        sHtml += "          <div class=\"input-group\" style=\"height:40px\">";
        sHtml += "              <input type=\"text\" class=\"form-control entry_artist\" placeholder=\"Various Artists\" aria-label=\"Various Artists\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Artist\">";
        sHtml += "          </div>";
        sHtml += "      </div>";
        sHtml += "      <div class=\"col-sm-5 album\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Artist name\">";
        sHtml += "          <div class=\"input-group\">";
        sHtml += "              <div class=\"input-group\" style=\"height:40px\">";
        sHtml += "                 <input type=\"text\" class=\"form-control entry_album\" placeholder=\"Album\" aria-label=\"track\" value=\"\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Album\">";
        sHtml += "              </div>";
        sHtml += "          </div>";
        sHtml += "      </div>";
    }
    else if (data.playlist.type == 'artistalbum')
    {
         sHtml += "      <div class=\"col-sm-9\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Album title\">";
//        sHtml += "          <div class=\"input-group\" style=\"height:40px\">";
//        sHtml += "              <input type=\"text\" class=\"form-control entry_artist\" placeholder=\"Various Artists\" aria-label=\"Various Artists\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Artist\">";
//        sHtml += "          </div>";
        sHtml += "          <h4 class=\"align-middle\">";
        sHtml +=                unescape_string(data.title.playlist.artist) + " - " + unescape_string(data.title.playlist.album)
        sHtml += "          </h4>";
        sHtml += "      </div>";


    }





    if (data.playlist.type == 'splitalbum')
    {
        sHtml += "      <div class=\"col-sm-2\">";
        sHtml += "          <div class=\"input-group d-flex justify-content-end\" >";
        sHtml += "              <div class=\"dropdown alternate_videos\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Alternate videos\">";
        sHtml += "                  <button class=\"fa fa-list-ol fa-2x\" style=\"width: 100%; height:100%\" type=\"button\" data-toggle=\"dropdown\">";
        sHtml += "                  </button>";
        sHtml += "                  <ul class=\"dropdown-menu list scrollable-menu\" role=\"menu\">";
        sHtml += "                      <div class=\"current_alternate_video\">";

        sHtml += "                      </div>";
        sHtml += "                      <li class=\"dropdown-divider\"></li>";
        sHtml += "                      <div class=\"video_alternate_items\">";

        sHtml += "                      </div>";
        sHtml += "                      <div class=\"row\">";
        sHtml += "                          <div class=\"col-sm-12\">";
        sHtml += "                              <div class=\"input-group\">"
        sHtml += "                                  <input type=\"text\" class=\"form-control search\" placeholder=\"Search for...\" aria-label=\"Search for...\" value=\"\">"
        sHtml += "                                  <button class=\"fa fa-search ytSearch\" type=\"button\">"
        sHtml += "                                  </button>"
        sHtml += "                              </div>"
        sHtml += "                         </div>"
        sHtml += "                      </div>";
        sHtml += "                      <li class=\"dropdown-divider\"></li>";
        sHtml += "                      <div class=\"row\">";
        sHtml += "                          <div class=\"col-sm-5\">";
        sHtml += "                              <a class=\"dropdown-item stayVisiblePrev text-sm-center\" href=\"#\">  <i class=\"fa fa-arrow-left\" aria-hidden=\"true\"></i> </a>";
        sHtml += "                          </div>";
        sHtml += "                          <div class=\"col-sm-2\">";
        sHtml += "                              <a class=\"dropdown-item stayVisibleRefresh text-sm-center\" href=\"#\">";
        sHtml += "                                  <i class=\"fa fa-refresh fa-1x\" aria-hidden=\"true\"></i>";
        sHtml += "                              </a>";
        sHtml += "                          </div>";
        sHtml += "                          <div class=\"col-sm-5\">";
        sHtml += "                              <a class=\"dropdown-item stayVisibleNext text-sm-center\" href=\"#\">  <i class=\"fa fa-arrow-right\" aria-hidden=\"true\"></i> </a>";
        sHtml += "                          </div>";
        sHtml += "                      </div>";
        sHtml += "                  </ul>";
        sHtml += "              </div>";
    }
    else
    {
        sHtml += "      <div class=\"col-sm-1\">";
        sHtml += "          <div class=\"input-group d-flex justify-content-end\">";
    }



    sHtml += "              <i class=\"" + iconClass +"\" style=\"padding-right:10px\" aria-hidden=\"true\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Download method: Artist / Album\"></i>";
    sHtml += "              <div class=\"checkbox selectall\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Master select\">";
    sHtml += "                  <label style=\"font-size: 1.8em\">";
    sHtml += "                      <input class=\"selall\" type=\"checkbox\" value=\"\" checked>";
    sHtml += "                          <span class=\"cr\">";
    sHtml += "                              <i class=\"cr-icon fa fa-check\"></i>";
    sHtml += "                          </span>";
    sHtml += "                      </input>";
    sHtml += "                  </label>";
    sHtml += "              </div>";
    sHtml += "          </div>";
    sHtml += "      </div>";
    sHtml += "  </div>";


    sHtml += "  <div class=\"row\">";
    sHtml += "      <div class=\"col-sm-12\">";
    sHtml += "          <div class=\"progress progressbar-container\" style=\"width:100%\">";
    sHtml += "              <div class=\"progress-bar progress-bar-striped active progressValue\" role=\"progressbar\" aria-valuenow=\"" + data.playlist.progress + "\" aria-valuemin=\"0\" aria-valuemax=\"100\" style=\"width:" + data.playlist.progress + "%\">";

    if (parseFloat(data.playlist.import_progress).toFixed(2) <= 100.0)
    {
        sHtml += "                  <span>" + data.playlist.progress + "% download complete</span>";

    }
    else
    {
        sHtml += "                  <span>Loading track information " + data.playlist.import_progress + "%</span>";

    }
    sHtml += "              </div>";
    sHtml += "          </div>";
    sHtml += "      </div>";
    sHtml += "  </div>";
    sHtml += "</div>";
    sHtml += "<div id=\"item_" + data.id.internal + "\" class=\"collapse multi-collapse\" role=\"tabcard\" aria-labelledby=\"" + data.id.internal + "\">";
    sHtml += "</div>";
    $(sHtml).prependTo($('#queue'));

    if (data.playlist.type == 'splitalbum')
    {
        $("#item_" + data.id.internal).sortable({
            stop: function( ) {
    //          send message to server to say that you have changed position in the queue
                var ar = $("#item_" + data.id.internal).sortable('toArray')
                var payload = CreateDataItem(['custom'])
                payload.id.internal = data.id.internal
                payload.id.client = g_clientid
                payload.custom = ar
                ws.send(CreateData("server/sort/videolist", payload))
    //            send the whole list to the server, rebuild the items in the playlist to the correct array, then return
    //            the list here and update the data in it.
            }
        });
        $("#item_" + data.id.internal).disableSelection();
        console.log('data is:' + data.playlist.videoItem.title.video.youtube)
        if (data.playlist.videoItem.title.video.youtube != '')
        {
            $("#" + data.id.internal + " .align-middle.fullfile").text(unescape_string(data.playlist.videoItem.title.video.youtube))
            $("#" + data.id.internal + " .img-responsive.thumbnail").prop('src', data.playlist.videoItem.thumbnail.current.default)
            $("#" + data.id.internal + " .text-right.endTime").text('[' + unescape_string(data.playlist.videoItem.row.duration.formatted) + ']')
        }
        $("#" + data.id.internal + " .form-control.search").val(unescape_string(data.title.playlist.artist) + " - " + unescape_string(data.title.playlist.album) + ' Full album')

        if (data.title.video.youtube != '')
        {
            $("#" + data.id.internal + " .img-responsive.thumbnail").prop('src', data.thumbnail.current.default)
            $("#" + data.id.internal + " .align-middle.fullfile").text(unescape_string(data.title.video.youtube))
            $("#" + data.id.internal + " .text-right.endTime").text('[' + unescape_string(data.row.duration.formatted) + ']')
        }

    }
    else
    {
        $("#" + data.id.internal + " .form-control.search").val(unescape_string(data.title.playlist.artist) + " - " + unescape_string(data.title.playlist.album))


    }
    $("#" + data.id.internal + " .dropdown.alternate_videos").on('show.bs.dropdown', function (e) {
        var payload = CreateDataItem(['results', 'download.video', 'row'])
        var searchterm = $("#" + data.id.internal + " .form-control.search").val()
        console.log("Searching for: " + searchterm)
        payload.results.searchterm = searchterm
        payload.results.target = "#" + data.id.internal + " .video_alternate_items"

        payload.id.client = g_clientid
        payload.id.internal = data.id.internal
//        payload.id.video = data.id.video
//        payload.download.current.videoId = data.download.current.videoId
        g_iStart = 0
        g_iEnd = 5
        payload.results.itemrange = [g_iStart,g_iEnd]
        ws.send(CreateData("server/get/searchvideo", payload))
    })
    $("#" + data.id.internal + " .dropdown.alternate_videos").on('hidden.bs.dropdown', function (e) {
        $("#" + data.id.internal + " .dropdown .video_alternate_items").empty()
    })

    $("#" + data.id.internal + " .fa.fa-list-ol.ytSearch").on('click', function (e) {
        var payload = CreateDataItem(['results', 'download.video', 'row'])
        var searchterm = $("#" + data.id.internal + " .form-control.search").val()
//        $("#" + data.id.internal + "_" + data.id.video  + " .dropdown .video_alternate_items").empty()

        payload.results.searchterm = searchterm
        payload.results.target = "#" + data.id.internal + " .video_alternate_items"
        payload.id.client = g_clientid
        payload.id.internal = data.id.internal
        payload.id.video = data.id.video
        payload.download.current.videoId = data.download.current.videoId
        payload.row.tracknumber = data.row.tracknumber

        g_iStart = 0
        g_iEnd = 5
        payload.results.itemrange = [g_iStart,g_iEnd]
        ws.send(CreateData("server/get/searchvideo", payload))
        e.stopPropagation()

    });

     $("#" + data.id.internal + " .dropdown-item.stayVisibleNext").click(function(e) {
//            console.log("Get 5 next and update the dropdownlist")
            var payload = CreateDataItem(['results', 'download.video', 'row'])
            var searchterm = $("#" + data.id.internal + " .form-control.search").val()
            g_iStart += 5
            g_iEnd += 5
            payload.results.searchterm = searchterm
            payload.results.target = "#" + data.id.internal + " .video_alternate_items"
            payload.id.client = g_clientid
            payload.id.internal = data.id.internal
//            payload.id.video = data.id.video
//            payload.download.current.videoId = data.download.current.videoId
//            payload.row.tracknumber = data.row.tracknumber
            payload.results.itemrange = [g_iStart,g_iEnd]
            ws.send(CreateData("server/get/searchvideo", payload))
            e.stopPropagation();
    });


    $("#" + data.id.internal + " .dropdown-item.stayVisiblePrev").click(function(e) {
//            console.log("Get 5 next and update the dropdownlist")
//            var start = parseInt($("#altvideos").children().first().attr("data-index-type"))-5
//            var end = parseInt($("#altvideos").children().last().attr("data-index-type"))-5
            var payload = CreateDataItem(['results', 'download.video', 'row'])
            var searchterm = $("#" + data.id.internal + " .form-control.search").val()

            if (g_iStart-5 < 0)
            {
                g_iStart = 0
                g_iEnd = 5
            }
            else
            {
                g_iStart -= 5
                g_iEnd -= 5

            }
            payload.results.searchterm = searchterm
            payload.results.target = "#" + data.id.internal + " .video_alternate_items"

            payload.id.client = g_clientid
            payload.id.internal = data.id.internal
//            payload.id.video = data.id.video
//            payload.download.current.videoId = data.download.current.videoId
//            payload.row.tracknumber = data.row.tracknumber
            payload.results.itemrange = [g_iStart,g_iEnd]
            ws.send(CreateData("server/get/searchvideo", payload))

            e.stopPropagation();
    });



    $("#" + data.id.internal + " .checkbox.selectall .selall").on('click', function (e) {

        var payload = CreateDataItem(['custom', 'row'])
        payload.id.internal = data.id.internal
        payload.id.video = data.id.video
        payload.id.client = g_clientid
        var checked = $("#" + data.id.internal + " .checkbox.selectall .selall").prop('checked')
        payload.row.selected = checked

        ws.send(CreateData("server/set/allselection", payload));


    });

    if (parseFloat(data.playlist.import_progress).toFixed(2) < 100.0)
    {
        $("#" + data.id.internal + " .fa.fa-play-circle.fa-2x.start").prop('disabled', true)
        $("#" + data.id.internal + " .btn.btn-sm.toggle").prop('disabled', true)
        $("#" + data.id.internal + " .fa.fa-trash-o.fa-2x.delete").prop('disabled', true)
        SetSpinner(true, "fa fa-chevron-right", "#" + data.id.internal + "_toggle")
    }
    else if (parseFloat(data.playlist.progress).toFixed(2) < 100 && (parseFloat(data.playlist.progress).toFixed(2) > 0))
    {
        SetSpinner(true, "fa fa-play-circle", "#" + data.id.internal + "_start")
    }
    $("#" + data.id.internal + " .fa.fa-play-circle.fa-2x.start").on('click', function (e) {
        console.log("starting item")
        var payload = CreateDataItem(['playlist.playlist', 'title.playlist'])
        payload.id.internal = data.id.internal
        payload.playlist.type = data.playlist.type
        payload.title.playlist.artist = $("#" + data.id.internal + " .entry_artist").val()
        payload.title.playlist.album = $("#" + data.id.internal + " .entry_album").val()
        SetSpinner(true, "fa fa-play-circle", "#" + data.id.internal + "_start")
        ws.send(CreateData('server/process/playlist', payload));
    });

    $("#" + data.id.internal + " .fa.fa-trash-o.fa-2x.delete").on('click', function (e) {
        console.log("removing item")
        var payload = CreateDataItem([])
        payload.id.internal = data.id.internal
        ws.send(CreateData('server/remove/playlist', payload));


    });


    if (data.title.playlist.album != undefined)
    {
        $("#" + data.id.internal + " .artist").innerHTML = unescape_string(data.title.playlist.album)
    }

    if (data.playlist.type == 'playlist' )
    {
        if (data.title.playlist.album != "-1")
        {
            $("#" + data.id.internal + " .entry_album").val(unescape_string(data.title.playlist.album))
        }
        if (data.title.playlist.artist != "-1")
        {
            $("#" + data.id.internal + " .entry_artist").val(unescape_string(data.title.playlist.artist))
        }
    }
    else if (data.playlist.type == 'splitalbum' || data.playlist.type == 'artistalbum')
    {
        if (data.title.playlist.album != "-1")
        {
            $("#" + data.id.internal + " .entry_album").val(unescape_string(data.title.playlist.album))
        }
        if (data.title.playlist.artist != "-1")
        {
            $("#" + data.id.internal + " .entry_artist").val(unescape_string(data.title.playlist.artist))
        }


    }

    if (data.playlist.type == 'splitalbum')
    {
        $("#" + data.id.internal + " .text-right.startTime").text("["+ data.playlist.duration.formatted + "]")
    }
    var icon = $("#" + data.id.internal + " .toggler").find('.fa.toggle')


    $("#item_" + data.id.internal).on('show.bs.collapse', function (e) {

        if (g_waiting_to_show[data.id.internal] == false)
        {
         console.log("Pressed toggle button")
            var payload = CreateDataItem([])

            payload.id.client = g_clientid
            payload.id.internal = data.id.internal
            // send the request to the server to get the videos
            ws.send(CreateData('server/get/videos', payload));


            g_waiting_to_show[data.id.internal] = true;
            icon.removeClass('fa fa-chevron-right fa-2x')
            icon.addClass('fa fa-chevron-down fa-2x')
            e.preventDefault();
        }
     });
     $("#item_" + data.id.internal).on('shown.bs.collapse', function (e) {
        g_waiting_to_show[data.id.internal] = false;
     });
     $("#item_" + data.id.internal).on(' hidden.bs.collapse', function (e) {
         $("#item_" + data.id.internal).empty();
     });

     $("#item_" + data.id.internal).on(' hide.bs.collapse', function (e) {
        icon.removeClass('fa fa-chevron-down fa-2x')
        icon.addClass('fa fa-chevron-right fa-2x')
     });

     $("#" + data.id.internal + " .entry_artist").keyup(function( event ) {
          var payload = CreateDataItem(['title.playlist'])
          payload.title.playlist.artist = $(this).val()
          payload.id.client = g_clientid
          payload.id.internal = data.id.internal
          ws.send(CreateData("server/set/artist", payload))
          if ( event.which == 13 ) {
             event.preventDefault();
          }
     });

     $("#" + data.id.internal + " .entry_album").keyup(function( event ) {
          var payload = CreateDataItem(['title.playlist'])
          payload.title.playlist.album = $(this).val()
          payload.id.client = g_clientid
          payload.id.internal = data.id.internal
          ws.send(CreateData("server/set/album", payload))
          if ( event.which == 13 ) {
             event.preventDefault();
          }
     });



}
function CreateSingleVideoEntry(type, data)
{
    var durationStatus = "same"


    if ('musicbrainz' in data)
    {
        if (type != 'splitalbum')
        {
            if (Math.abs(data.row.duration.seconds-data.musicbrainz.duration.seconds) > 5)
            {
                durationStatus = "different"

            }
        }
    }


var sHtml="";
//    console.log("\""+ data.tracknumber + " - " + unescape_string(data.title) + "\"")
    sHtml += "<div id=\"" + data.id.internal + "_" + data.id.video + "\" class=\"row\">";





    if (type == 'splitalbum')
    {
        sHtml += "      <div class=\"col-sm-4\">";
    }
    else
    {
        sHtml += "      <div class=\"col-sm-5\">";
    }

    sHtml += "          <div class=\"input-group\" style=\"height:50px\">";
    sHtml += "              <span class=\"input-group-addon tracknumber\" style=\"width:50px\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Track number\">" + data.row.tracknumber +  "</span>";
    if (type == 'splitalbum')
    {

        sHtml += "              <input type=\"text\" class=\"form-control duration start\" placeholder=\"Track duration start\" aria-label=\"track\" value=\"\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Track duration start\">";
        sHtml += "              <input type=\"text\" class=\"form-control duration end\" placeholder=\"Track duration end\" aria-label=\"track\" value=\"\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Track duration end\">";
//        sHtml += "              <input type=\"text\" class=\"form-control duration offset\" placeholder=\"offset\" aria-label=\"track\" value=\"\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Track offset\">";

//        sHtml += "              <span class=\"input-group-addon duration\" style=\"width:90px\"data-toggle=\"tooltip\" data-placement=\"top\" title=\"Track duration\">" + data.row.duration.formatted + "</span>";
    }
    else
    {
        sHtml += "              <span class=\"input-group-addon duration\" style=\"width:90px\"data-toggle=\"tooltip\" data-placement=\"top\" title=\"Track duration\">" + data.row.duration.formatted + "</span>";
        sHtml += "              <input type=\"text\" class=\"form-control track\" placeholder=\"Track title\" aria-label=\"track\" value=\"\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Track title\">";
    }

    sHtml += "          </div>";



    sHtml += "      </div>";
//    if (type == 'splitalbum')
//    {
//        sHtml += "      <div class=\"col-sm-1\">";
//
//        sHtml += "      </div>";
//    }


    if (type != 'splitalbum')
    {
        sHtml += "      <div class=\"col-sm-4\">";
        sHtml += "          <div class=\"input-group\" style=\"height:50px\">";
        if ('musicbrainz' in data)
        {
            sHtml += "              <span class=\"input-group-addon videoduration " + durationStatus + "\" style=\"width:90px\"data-toggle=\"tooltip\" data-placement=\"top\" title=\"video duration\">" + data.musicbrainz.duration.formatted + "</span>";
        }
        else
        {
            sHtml += "              <span class=\"input-group-addon videoduration " + durationStatus + "\" style=\"width:90px\"data-toggle=\"tooltip\" data-placement=\"top\" title=\"video duration\">" + data.row.duration.formatted + "</span>";
        }

        sHtml += "              <input type=\"text\" class=\"form-control video\" placeholder=\"Video title\" aria-label=\"video\" value=\"\" readonly data-toggle=\"tooltip\" data-placement=\"top\" title=\"Youtube video title\">";
        sHtml += "              <span class=\"input-group-addon\">";
        sHtml += "                  <img style=\"height:50px\" src=\"\" class=\"img-responsive thumbnail\">";
        sHtml += "              </span>";
        sHtml += "              <div class=\"dropdown alternate_videos\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Alternate videos\">";
        sHtml += "                  <button class=\"fa fa-list-ol fa-2x\" style=\"width: 100%; height:100%\" type=\"button\" data-toggle=\"dropdown\">";
        sHtml += "                  </button>";
        sHtml += "                  <ul class=\"dropdown-menu list scrollable-menu\" role=\"menu\">";
        sHtml += "                      <div class=\"current_alternate_video\">";

        sHtml += "                      </div>";
        sHtml += "                      <li class=\"dropdown-divider\"></li>";
        sHtml += "                      <div class=\"video_alternate_items\">";

        sHtml += "                      </div>";
        sHtml += "                      <div class=\"row\">";
        sHtml += "                          <div class=\"col-sm-12\">";
        sHtml += "                              <div class=\"input-group\">"
        sHtml += "                                  <input type=\"text\" class=\"form-control search\" placeholder=\"Search for...\" aria-label=\"Search for...\" value=\"\">"
        sHtml += "                                  <button class=\"fa fa-search ytSearch\" type=\"button\">"
        sHtml += "                                  </button>"
        sHtml += "                              </div>"
        sHtml += "                         </div>"
        sHtml += "                      </div>";


        sHtml += "                      <li class=\"dropdown-divider\"></li>";
        sHtml += "                      <div class=\"row\">";
        sHtml += "                          <div class=\"col-sm-5\">";
        sHtml += "                              <a class=\"dropdown-item stayVisiblePrev text-sm-center\" href=\"#\">  <i class=\"fa fa-arrow-left\" aria-hidden=\"true\"></i> </a>";
        sHtml += "                          </div>";
        sHtml += "                          <div class=\"col-sm-2\">";
        sHtml += "                              <a class=\"dropdown-item stayVisibleRefresh text-sm-center\" href=\"#\">";
        sHtml += "                                  <i class=\"fa fa-refresh fa-1x\" aria-hidden=\"true\"></i>";
        sHtml += "                              </a>";
        sHtml += "                          </div>";
        sHtml += "                          <div class=\"col-sm-5\">";
        sHtml += "                              <a class=\"dropdown-item stayVisibleNext text-sm-center\" href=\"#\">  <i class=\"fa fa-arrow-right\" aria-hidden=\"true\"></i> </a>";
        sHtml += "                          </div>";
        sHtml += "                      </div>";
        sHtml += "                  </ul>";
        sHtml += "              </div>";
        sHtml += "          </div>";
        sHtml += "      </div>";
    }
    else
    {
        sHtml += "      <div class=\"col-sm-5\">";
        sHtml += "          <div class=\"input-group\" style=\"height:50px\">";
        sHtml += "              <input type=\"text\" class=\"form-control track\" placeholder=\"Track title\" aria-label=\"track\" value=\"\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Track title\">";
        sHtml += "          </div>";
        sHtml += "      </div>";
    }
    sHtml += "      <div class=\"col-sm-3\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Status\">";
    sHtml += "          <div class=\"input-group status text-sm-center\" style=\"height:50px\">";
    sHtml += "              <input type=\"text\" class=\"form-control text-sm-center status\" placeholder=\"status\" aria-label=\"video\" value=\"" + data.row.status + "\" readonly>";
    sHtml += "              <div class=\"userinfo_parent\">";
//    gives additional info about the video entry here... using icons?
    if (data.row.modified)
    {
        sHtml += "                  <span class=\"input-group-addon userinfo\" style=\"height:50px\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"stats\">"
        sHtml += "                      <i class=\"fa fa-pencil fa-1x\" aria-hidden=\"true\"></i>";
        sHtml += "                  </span>";
    }
    sHtml += "              </div>";
    sHtml += "              <div class=\"checkbox selected\" data-toggle=\"tooltip\" data-placement=\"top\" title=\"Include in download\">";
    sHtml += "                  <label style=\"font-size: 2.5em\">";
    sHtml += "                      <input class=\"sel\" type=\"checkbox\" value=\"\" checked>";
    sHtml += "                          <span class=\"cr\">";
    sHtml += "                              <i class=\"cr-icon fa fa-check\"></i>";
    sHtml += "                          </span>";
    sHtml += "                      </input>";
    sHtml += "                  </label>";
    sHtml += "              </div>";
    sHtml += "          </div>";
    sHtml += "      </div>";
    sHtml += "</div>";
    $(sHtml).appendTo($("#item_" + data.id.internal));


    if (type == 'splitalbum')
        {
//              $("#" + data.id.internal + "_" + data.id.video + " .form-control.duration.start").keyup(function( event ) {
//                  var payload = CreateDataItem(['row'])
//                  payload.row.offset.formatted = $(this).val()
//                  var tokens = payload.row.offset.formatted.split(':')
//                  var bProceed = true
//                  if (tokens.length == 3)
//                  {
//                    for (i = 0;i<tokens.length;i++)
//                    {
//                        if (isNumeric(tokens[i]) == false)
//                        {
//                            bProceed = false
//
//                        }
//                    }
//                  }
//                  else
//                  {
//                    bProceed = false
//                  }
//
//                  if (bProceed)
//                  {
//                      payload.id.client = g_clientid
//                      payload.id.internal = data.id.internal
//                      payload.id.video = data.id.video
//                      console.log('sending:' + payload.row.offset.formatted)
//                      if ( event.which == 13 ) {
//
//                          ws.send(CreateData("server/set/splitalbum/track/offset", payload))
//                          event.preventDefault();
//                      }
//                  }
//              });

              $("#" + data.id.internal + "_" + data.id.video + " .form-control.duration.end").keyup(function( event ) {
                  var payload = CreateDataItem(['row'])

                  var bProceed = true




                  var silenceToken = $(this).val().split('|')
                  if (silenceToken.length == 2)
                  {
                    if (isNumeric(silenceToken[1]) == false)
                    {
                        bProceed = false
                    }
                  }
                  else
                  {
                    bProceed = false
                  }



                  var tokens = silenceToken[0].split(':')

                  if (tokens.length == 3)
                  {
                    for (i = 0;i<tokens.length;i++)
                    {
                       if (isNumeric(tokens[i]) == false)
                        {
                            bProceed = false
                        }
                    }
                  }
                  else
                  {
                    bProceed = false
                  }

                  if (bProceed)
                  {
                      payload.row.silence.seconds = parseInt(silenceToken[1])
                      payload.row.duration.formatted = silenceToken[0]
                      payload.id.client = g_clientid
                      payload.id.internal = data.id.internal
                      payload.id.video = data.id.video
                      console.log('sending:' + payload.row.duration.formatted)
                      ws.send(CreateData("server/set/splitalbum/track/duration", payload))
                      if ( event.which == 13 ) {


                          event.preventDefault();
                      }
                  }
              });

    }
    $("#" + data.id.internal + "_" + data.id.video + " .dropdown-item.stayVisibleNext").click(function(e) {
//            console.log("Get 5 next and update the dropdownlist")
//            var start = parseInt($("#altvideos").children().first().attr("data-index-type"))+5
//            var end = parseInt($("#altvideos").children().last().attr("data-index-type"))+5
            var payload = CreateDataItem(['results', 'download.video', 'row'])
            var searchterm = $("#" + data.id.internal + "_" + data.id.video + " .form-control.search").val()
            g_iStart += 5
            g_iEnd += 5
            payload.results.searchterm = searchterm
            payload.results.target = "#" + data.id.internal + "_" + data.id.video + " .video_alternate_items"
            payload.id.client = g_clientid
            payload.id.internal = data.id.internal
            payload.id.video = data.id.video
            payload.download.current.videoId = data.download.current.videoId
            payload.row.tracknumber = data.row.tracknumber
            payload.results.itemrange = [g_iStart,g_iEnd]

            ws.send(CreateData("server/get/searchvideo", payload))

            e.stopPropagation();
    });


    $("#" + data.id.internal + "_" + data.id.video + " .dropdown-item.stayVisiblePrev").click(function(e) {
//            console.log("Get 5 next and update the dropdownlist")
//            var start = parseInt($("#altvideos").children().first().attr("data-index-type"))-5
//            var end = parseInt($("#altvideos").children().last().attr("data-index-type"))-5
            var payload = CreateDataItem(['results', 'download.video', 'row'])
            var searchterm = $("#" + data.id.internal + "_" + data.id.video + " .form-control.search").val()

            if (g_iStart-5 < 0)
            {
                g_iStart = 0
                g_iEnd = 5
            }
            else
            {
                g_iStart -= 5
                g_iEnd -= 5

            }
            payload.results.searchterm = searchterm
            payload.results.target = "#" + data.id.internal + "_" + data.id.video + " .video_alternate_items"

            payload.id.client = g_clientid
            payload.id.internal = data.id.internal
            payload.id.video = data.id.video
            payload.download.current.videoId = data.download.current.videoId
            payload.row.tracknumber = data.row.tracknumber
            payload.results.itemrange = [g_iStart,g_iEnd]
            ws.send(CreateData("server/get/searchvideo", payload))

            e.stopPropagation();
    });





    $("#" + data.id.internal + "_" + data.id.video  + " .checkbox.selected .sel").prop('checked', data.row.selected)
    $("#" + data.id.internal + "_" + data.id.video  + " .checkbox.selected .sel").on('click', function (e) {
        var payload = CreateDataItem(['row'])
        payload.id.internal = data.id.internal
        payload.id.video = data.id.video
        payload.id.client = g_clientid
        var checked = $("#" + data.id.internal + "_" + data.id.video  + " .checkbox.selected .sel").prop('checked')
        payload.row.selected = checked

        ws.send(CreateData("server/set/selected", payload));


    });
    $("#" + data.id.internal + "_" + data.id.video  + " .form-control.track").val(unescape_string(data.title.video.track))

    if (data.title.video.youtube == '')
    {
        $("#" + data.id.internal + "_" + data.id.video  + " .form-control.video").val(unescape_string(data.title.video.original))
    }
    else
    {
        $("#" + data.id.internal + "_" + data.id.video  + " .form-control.video").val(unescape_string(data.title.video.youtube))
    }

    if (type == 'splitalbum')
    {
        $("#" + data.id.internal + "_" + data.id.video  + " .form-control.duration.start").val(data.row.offset.formatted)
        $("#" + data.id.internal + "_" + data.id.video  + " .form-control.duration.end").val(data.row.duration.formatted + "|" + data.row.silence.seconds.toString())
    }


    if ('musicbrainz' in data)
    {
       if (data['musicbrainz']['artist'] != '')
       {
            $("#" + data.id.internal + "_" + data.id.video  + " .form-control.search").val(unescape_string(data.musicbrainz.artist) + " - " + unescape_string(data.title.video.original))
       }
       else
       {
            $("#" + data.id.internal + "_" + data.id.video  + " .form-control.search").val(unescape_string(data.title.video.original))
       }
    }
    else
    {
        $("#" + data.id.internal + "_" + data.id.video  + " .form-control.search").val(unescape_string(data.title.video.original))
    }


    $("#" + data.id.internal + "_" + data.id.video  + " .thumbnail").prop('src', data.thumbnail.current.default)


    var menu = new BootstrapMenu("#" + data.id.internal + "_" + data.id.video  + " .form-control.track", {
      actions: [{
          name: 'Filter phrase',
          onClick: function() {
            // run when the action is clicked
            var text = "";
            if (window.getSelection) {
                text = window.getSelection().toString();
            } else if (document.selection && document.selection.type != "Control") {
                text = document.selection.createRange().text;
            }
            var payload = CreateDataItem('filter')
            payload.filter.key = text
            payload.filter.value = ''
            ws.send(CreateData("server/add/filteritem", payload));
          }
        }
        , {
          name: 'Reset',
          onClick: function() {
//                $("#" + data.internalId + "_" + data.internal_videoId  + " .form-control.track").val(data.tracknumber + " - " + unescape_string_v2(data.original_title))
//                console.log(unescape_string(data.original_title))
//                $("#" + data.internalId + "_" + data.internal_videoId  + " .form-control.track").trigger('keyup')
                  var payload = CreateDataItem(['title.video', 'download.video', 'row', 'custom'])
                  if (data.title.video.youtube == '')
                  {
                    payload.title.video.track = data.title.video.original
                  }
                  else
                  {
                    payload.title.video.track = data.title.video.youtube
                  }

                  payload.id.client = g_clientid
                  payload.id.internal = data.id.internal
                  payload.id.video = data.id.video
                  payload.download.current.videoId = data.download.current.videoId
                  payload.row.tracknumber = data.row.tracknumber
                  payload.custom.reset = true
//                  console.log("Resetting:")
//                  console.log(payload)
                  ws.send(CreateData("server/set/tracktitle", payload));


            }
        }
        ]
    });
    $("#" + data.id.internal + "_" + data.id.video + " .fa.fa-search.ytSearch").on('click', function (e) {
        var payload = CreateDataItem(['results', 'download.video', 'row'])
        var searchterm = $("#" + data.id.internal + "_" + data.id.video + " .form-control.search").val()
//        $("#" + data.id.internal + "_" + data.id.video  + " .dropdown .video_alternate_items").empty()

        payload.results.searchterm = searchterm
        payload.id.client = g_clientid
        payload.id.internal = data.id.internal
        payload.id.video = data.id.video
        payload.download.current.videoId = data.download.current.videoId
        payload.row.tracknumber = data.row.tracknumber
        g_iStart = 0
        g_iEnd = 5
        payload.results.itemrange = [g_iStart,g_iEnd]
        ws.send(CreateData("server/get/searchvideo", payload))
        e.stopPropagation()

    });
    $("#" + data.id.internal + "_" + data.id.video + " .form-control.track").keyup(function( event ) {
          var payload = CreateDataItem(['title.video', 'download.video', 'row', 'custom'])
          payload.title.video.track = $(this).val()
          payload.id.client = g_clientid
          payload.id.internal = data.id.internal
          payload.id.video = data.id.video
          payload.download.current.videoId = data.download.current.videoId
          payload.row.tracknumber = data.row.tracknumber
          payload.custom.reset = false
          ws.send(CreateData("server/set/tracktitle", payload))

          if ( event.which == 13 ) {
             event.preventDefault();
          }
    });

    $("#" + data.id.internal + "_" + data.id.video + " .dropdown.alternate_videos").on('show.bs.dropdown', function (e) {
        var payload = CreateDataItem(['results', 'download.video', 'row'])
        var searchterm = $("#" + data.id.internal + "_" + data.id.video + " .form-control.search").val()
        payload.results.searchterm = searchterm
        payload.results.target = "#" + data.id.internal + "_" + data.id.video + " .video_alternate_items"
        payload.id.client = g_clientid
        payload.id.internal = data.id.internal
        payload.id.video = data.id.video
        payload.download.current.videoId = data.download.current.videoId
        payload.row.tracknumber = data.row.tracknumber
        g_iStart = 0
        g_iEnd = 5
        payload.results.itemrange = [g_iStart,g_iEnd]

        ws.send(CreateData("server/get/searchvideo", payload))




    })
    $("#" + data.id.internal + "_" + data.id.video  + " .dropdown.alternate_videos").on('hidden.bs.dropdown', function (e) {
        $("#" + data.id.internal + "_" + data.id.video  + " .dropdown .video_alternate_items").empty()
    })



    var payload = CreateDataItem(['title.video', 'thumbnail', 'download.video', 'results', 'row', 'custom'])
    payload.title.video.youtube = unescape_string(data.title.video.original)
    payload.results.description = "Hello world"
    payload.results.index = -1

    if ('musicbrainz' in data)
    {
        payload.results.duration.formatted = data.musicbrainz.duration.formatted
    }
    else
    {
        payload.results.duration.formatted = data.row.duration.formatted
    }
    payload.thumbnail.current.default = data.thumbnail.current.default
    payload.id.internal = data.id.internal
    payload.id.video = data.id.video
    payload.download.current.videoId = data.download.original.videoId
    payload.custom.isoriginal = true
    payload.row.tracknumber = data.row.tracknumber

    CreateAlternateVideos(payload, '#' + payload.id.internal + '_' + payload.id.video + ' .current_alternate_video')
}
//function GenerateEntries()
//{
//    for (var element in g_data.items)
//    {
////        console.log(g_data.items[element])
//        CreateSinglePlaylistEntry(g_data.items[element])
//    }
//}
function SetSpinner(bSpinnerSet, resetIcon, target)
{

    var element = $(target)
    if (bSpinnerSet)
    {


        element.removeClass(resetIcon)
        element.addClass("fa fa-spinner fa-spin")
        element.prop('disabled', true)

    }
    else
    {
        element.removeClass("fa fa-spinner fa-spin")
        element.addClass(resetIcon)
        element.prop('disabled', false)
    }
}
$(document).ready(function () {

        $("#clearcache").on('click', function(e) {
            console.log("clearing cache")
            var modalform = $("#modal_form")
            modalform.find('.modal-title').text("Clear cache")
            modalform.prop('data-type', "clearcache")
            modalform.find('.modal-body').text("Are you sure you want to clear search cache?")
            modalform.modal('show')
        });
        $("#clearalltasks").on('click', function(e) {
            console.log("clearing cache")
            var modalform = $("#modal_form")
            modalform.find('.modal-title').text("Clear all tasks")
            modalform.prop('data-type', "clearall")
            modalform.find('.modal-body').text("Are you sure you want to clear all tasks?")
            modalform.modal('show')
        });
        $("#clearcompleted").on('click', function(e) {
            console.log("clearing completed tasks")
            var modalform = $("#modal_form")
            modalform.find('.modal-title').text("Remove completed tasks")
            modalform.prop('data-type', "removecompleted")
            modalform.find('.modal-body').text("Are you sure you want to clear all completed tasks?")
            modalform.modal('show')
        });
        $("#modal_form_confirm").on('click', function(e) {
            $("#modal_form").prop('data-confirm', true)
        });
        $("#modal_form").on('show.bs.modal', function(e) {
            $(this).prop('data-confirm', false)
        })
        $("#modal_form").on('hidden.bs.modal', function(e) {

            if ($(this).prop('data-confirm'))
            {
                var payload = CreateDataItem([])
                payload.id.client = g_clientid
                switch($("#modal_form").prop('data-type'))
                {
                    case "removecompleted":
                        console.log($("#modal_form").prop('data-type'))
                        ws.send(CreateData("server/remove/completedtasks", payload))
                    break;
                    case "clearcache":
                        console.log($("#modal_form").prop('data-type'))
                        ws.send(CreateData("server/remove/cache", payload))
                    break;
                    case "clearall":
                        console.log($("#modal_form").prop('data-type'))
                        ws.send(CreateData("server/remove/alltasks", payload))
                    break;
                }

            }

        })


        $("#filter_playlist").on('click', function(e) {
            if ($(this).hasClass("btn-danger") == false)
            {
//                console.log("filtering out all youtube playlists")
                var payload = CreateDataItem(['custom'])
                payload.id.client = g_clientid
                payload.items = []
                payload.custom.filter_playlist = true
                if ($("#filter_artistalbum").hasClass("btn-danger"))
                {
                    payload.custom.filter_artistalbum = true
                }
                ws.send(CreateData("server/get/playlists", payload))
            }
            else
            {
//                console.log("including all youtube playlists")
                var payload = CreateDataItem(['custom'])
                payload.id.client = g_clientid
                payload.items = []
                if ($("#filter_artistalbum").hasClass("btn-danger"))
                {
                    payload.custom.filter_artistalbum = true
                }
                ws.send(CreateData("server/get/playlists", payload))
            }

        });
        $("#filter_artistalbum").on('click', function(e) {
            if ($(this).hasClass("btn-danger") == false)
            {
//                console.log("filtering out all youtube playlists")
                var payload = CreateDataItem(['custom'])
                payload.id.client = g_clientid
                payload.items = []
                payload.custom.filter_artistalbum = true
                if ($("#filter_playlist").hasClass("btn-danger"))
                {
                    payload.custom.filter_playlist = true
                }
                ws.send(CreateData("server/get/playlists", payload))
            }
            else
            {
//                console.log("including all youtube playlists")
                var payload = CreateDataItem(['custom'])
                payload.id.client = g_clientid
                payload.items = []
                if ($("#filter_playlist").hasClass("btn-danger"))
                {
                    payload.custom.filter_playlist = true
                }
                ws.send(CreateData("server/get/playlists", payload))
            }

        });



        $("#mb_search").on('show.bs.dropdown', function (e) {
            console.log("sending search to music brainz")
            if (g_waiting_to_show[g_clientid] == false)
            {
                var artist = jQuery.trim($("#input_artist").val())
                var album = jQuery.trim($("#input_album").val())
                if (artist != '' && album != '')
                {
                    g_waiting_to_show[g_clientid] = true;
                    var payload = CreateDataItem(['results'])
                    payload.id.client = g_clientid
                    payload.results.searchterm = new Object()
                    payload.results.searchterm.artist = artist
                    payload.results.searchterm.album = album
                    ws.send(CreateData("server/get/mbalbums", payload))
                    SetSpinner(true, "fa fa-search", "#mb_searchIcon")

//                    $("#mbsearchIcon").removeClass("fa fa-search")
//                    $("#mbsearchIcon").addClass("fa fa-spinner fa-spin")

                    e.stopPropagation()
                }
            }
        });
        $("#mb_search").on('shown.bs.dropdown', function (e) {
            g_waiting_to_show[g_clientid] = false;
        });
        $("#filter_list").on('show.bs.dropdown', function (e) {
//            request the filtered list from the backend
            var payload = CreateDataItem([])
            payload.id.client = g_clientid
            g_filter_is_open = true
            ws.send(CreateData("server/get/filterlist", payload))


        });
        $("#filter_list").on('hidden.bs.dropdown', function (e) {
//            request the filtered list from the backend
            $("#filter_list .filter_items").empty()
            g_filter_is_open = false

        });
        $("#add_task").hide()
        $('#add_task').on('click', function(){
//         var type = ($('#add_task').attr('data-index'))
         var payload = CreateDataItem(['title.playlist', 'playlist.playlist'])
         payload.playlist.type = 'playlist'
//         at this point no artist or album is defined. Only the playlistURL
         payload.playlist.url = $('#input_playlistURL').val()
         ws.send(CreateData("server/add/url", payload));
        });

        $('[data-toggle="buttons"] .btn').on('click', function () {
            // toggle style
            $(this).toggleClass('btn-success btn-danger active');

            // toggle checkbox
            var $chk = $(this).find('[type=checkbox]');
            $chk.prop('checked',!$chk.prop('checked'));

            return false;
        });
        $('[data-toggle="tooltip"]').tooltip({
                placement : 'top'
        });
        $('#dl_type .dropdown-menu .dropdown-item.normal').on('click', function(){
            $('#dl_type  .input-group-btn .btn-secondary:first-child').text("Add " + $(this).text())
            $('#add_task').text("Add " + $(this).text())
            $('#add_task').attr('data-index', $(this).attr("id"))

            if ($(this).attr("id") == "0")
            {
//                console.log("index 0")
                $('#input_artistalbum').hide()
                $('#input_playlistURL').show()
                $("#add_task").show()
                $("#add_task").parent().prop('style', 'height:38px')
                $("#task_type").parent().prop('style', 'height:38px')
                $('#mb_search').hide()
                g_dltype = 0;


            }
            else if ($(this).attr("id") == "1" || ($(this).attr("id") == "2"))
            {
//                console.log("index 1")
                $('#input_artistalbum').show()
                $('#mb_search').show()

                $('#input_playlistURL').hide()
                $("#add_task").hide()

                $("#add_task").parent().prop('style', 'height:75px')
                $("#task_type").parent().prop('style', 'height:75px')
                g_dltype = parseInt($(this).attr("id"));
            }
        });


    });
