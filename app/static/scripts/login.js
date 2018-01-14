var ws;
function onLogin() {
    var hostname = window.location.hostname
    console.log(hostname)
    ws = new WebSocket("ws://" + hostname + ":8085/websocket");
    ws.onmessage = function(e) {
        loginHandler(e.data)
    };

}
function CreateDataItem(parts = [])
{
    var payload = new Object()
    if (parts.includes('login'))
    {
        payload.login = new Object()
        payload.login.user = ''
        payload.login.password = ''
    }
};
function loginHandler(data) {
     jsonData = JSON.parse(data)
     payload = jsonData['payload']

     if (jsonData.hasOwnProperty('type'))
     {
        switch(jsonData.type)
        {
            case 'client/login/response':


            break;



        }
     }


}
function CreateData(type, payload)
{
    var data = new Object();
    data.type = type;
    data.payload = payload;
    var jsonString = JSON.stringify(data);
//    console.log("Sending:" + jsonString)
    return jsonString
}
$(document).ready(function () {
    $("#submit").on('click', function(e){
        var payload = CreateDataItem(['login'])
        payload.user = $('#email').val()
        payload.password = $('#password').val()
        ws.send(CreateData("server/login", payload))
    });
});