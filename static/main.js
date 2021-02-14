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

    fetch('/nornir', options)
        .then(
            function(response) {
                if (response.status !== 200) {
                    document.getElementById('output').innerHTML = "Unexpected error.  Try refreshing the page?";
                    console.log('Response Error. Status Code: ' + response.status);
                    return;
                }

                response.json().then( data => {
                    document.getElementById('output').innerHTML = data.output;
                    document.getElementById('submit').disabled = false;
                });
            }
        )
        .catch(function(err) {
            document.getElementById('output').innerHTML = "Unexpected error.  Try refreshing the page?";
            console.log('Fetch Error :-S', err);
        });
        
}

