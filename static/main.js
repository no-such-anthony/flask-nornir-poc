document.addEventListener("DOMContentLoaded", () => {

    document.getElementById("submit").addEventListener("click", () => {
        submitRun();
    });

    document.querySelectorAll("div[data-editor]").forEach( el => {
        let mode = el.dataset.editor;
        editor = ace.edit(el);
        editor.renderer.setShowGutter(false);
        editor.getSession().setMode("ace/mode/" + mode);
        editor.setTheme("ace/theme/twilight");
        editor.getSession().setTabSize(2);
        el.style.visibility = "visible";
    });

});

function submitRun() {

    document.getElementById("output").innerHTML = "<h2>running...</h2>";
    document.getElementById("submit").disabled = true;
    document.getElementById("progress").innerHTML = "";
    document.getElementById("updates").innerHTML = "";

    let formData = new FormData();
    formData.append('csrf_token', document.querySelector('input[name=csrf_token]').value);
    formData.append('today', document.querySelector('input[name=today]:checked').value);
    formData.append('hosts', ace.edit('hosts').getSession().getValue());
    formData.append('groups', ace.edit('groups').getSession().getValue());
    formData.append('defaults', ace.edit('defaults').getSession().getValue());

    const options = {
        method: 'POST',
        body: formData
    };

    startPoll();

    fetch('/nornir', options)
        .then(
            function(response) {
                if (response.status !== 200) {
                    document.getElementById('output').innerHTML = "Unexpected error.  Try refreshing the page?";
                    console.log('Response Error. Status Code: ' + response.status);
                    stopPoll();
                    return;
                }

                response.json().then( data => {
                    document.getElementById('output').innerHTML = data.output;
                    document.getElementById('submit').disabled = false;
                    stopPoll();
                    poll();
                });
            }
        )
        .catch(function(err) {
            document.getElementById('output').innerHTML = "Unexpected error.  Try refreshing the page?";
            console.log('Fetch Error :-S', err);
            stopPoll();
        });

}

let myPollTimer

function stopPoll() {
    clearInterval(myPollTimer);
}

function startPoll() {
    myPollTimer = setInterval(poll, 5000);
}

function poll() {

    console.log("polling");
    fetch('/nornir/poll')
        .then(
            function(response) {
                if (response.status !== 200) {
                    document.getElementById('output').innerHTML = "Unexpected error.  Try refreshing the page?";
                    console.log('Response Error. Status Code: ' + response.status);
                    return;
                }

                response.json().then( data => {
                    document.getElementById('updates').innerHTML += data.updates;
                    if (data.progress!=='') {
                        document.getElementById('progress').innerHTML = data.progress;
                    }

                });
            }
        )
        .catch(function(err) {
            document.getElementById('output').innerHTML = "Unexpected error.  Try refreshing the page?";
            console.log('Fetch Error :-S', err);
        });

}

