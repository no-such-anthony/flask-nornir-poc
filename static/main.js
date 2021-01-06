$(document).ready(function() {

    //click behaviour for main buttons
    $('#submit').click(function() {
        submitRun(socket.id);
    });

    var socket = io();
    socket.on('connect', function() {
        console.log('client connected');
    });

    socket.on('update', function(msg) {
        $("#updates").append('<li>'+msg+'</li>');
    });

    socket.on('progress', function(msg) {
        $("#progress").html(msg).show();
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

function submitRun(socket_id) {
    // send ajax POST request to start background job
    $('#output').html("<h2>running...</h2>").show()
    $("#progress").html('').show();
    $("#updates li").remove();
    $("#submit").prop('disabled', true);

    var formData = {
        'csrf_token'        : $('input[name=csrf_token]').val(),
        'socket_id'         : socket_id,
        'today'             : $('input[name=today]:checked').val(),
        'hosts'             : ace.edit('hosts').getSession().getValue(),
        'groups'            : ace.edit('groups').getSession().getValue(),
        'defaults'          : ace.edit('defaults').getSession().getValue(),
    };

    $.ajax({
        type: 'POST',
        url: '/nornir',
        data: formData,
        success: function(data, status, request) {
            $('#output').html(data.output).show();
            $("#submit").prop('disabled', false);
        },
        error: function() {
            $('#output').html("Unexpected error.  Try refreshing the page.").show();
        }
    });


}

