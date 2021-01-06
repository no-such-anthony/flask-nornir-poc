$(document).ready(function() {

    //click behaviour for main buttons
    $('#submit').click(function() {
        submitRun();
    });

    $(function () {
        $('div[data-editor]').each(function () {
            var mode = $(this).data('editor');
            editor = ace.edit($(this)[0]);
            editor.renderer.setShowGutter(false);
            editor.getSession().setMode("ace/mode/" + mode);
            editor.setTheme("ace/theme/twilight");
            editor.getSession().setTabSize(2);
            $(this).css('visibility', 'visible');
        })
    })

});

function submitRun() {
    // send ajax POST request to start background job
    $('#output').html("<h2>running...</h2>").show()
    $("#progress").html('').show();
    $("#updates li").remove();
    $("#submit").prop('disabled', true);

    var formData = {
        'csrf_token'        : $('input[name=csrf_token]').val(),
        'today'             : $('input[name=today]:checked').val(),
        'hosts'             : ace.edit('hosts').getSession().getValue(),
        'groups'            : ace.edit('groups').getSession().getValue(),
        'defaults'          : ace.edit('defaults').getSession().getValue(),
    };

    startPoll();
    $.ajax({
        type: 'POST',
        url: '/nornir',
        data: formData,
        success: function(data, status, request) {
            $('#output').html(data.output).show();
            $("#submit").prop('disabled', false);
            stopPoll();
            poll();
        },
        error: function() {
            stopPoll();
            $('#output').html("Unexpected error.  Try refreshing the page.").show();
        }
    });

}

var myPollTimer

function stopPoll() {
    clearInterval(myPollTimer);
}

function startPoll() {
    myPollTimer = setInterval(poll, 5000);
}

function poll() {
    $.ajax({
        url: "/nornir/poll",
        type: "GET",
        success: function(data) {
            console.log("polling");
            $("#updates").append(data.updates);
            $("#progress").html(data.progress).show()
        },
        dataType: "json",
        timeout: 2000
    })

}

