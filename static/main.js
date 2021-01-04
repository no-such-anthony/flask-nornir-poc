$(document).ready(function() {

  //click behaviour for main buttons
  $('#submit').click(function() {
      submitRun(socket.id);
  });

  var socket = io();
  socket.on('connect', function() {
      socket.send('client connected');
  });

  socket.on('update', function(msg) {
      $("#updates").append('<li>'+msg+'</li>');
  });

  socket.on('progress', function(msg) {
    $("#progress").html(msg).show();
  });

});

function submitRun(socket_id) {
    // send ajax POST request to start background job
    $('#output').html("<h2>running...</h2>").show()
    $("#progress").html('').show();
    $("#updates li").remove();
    $("#submit").prop('disabled', true);
    $("#socket_id").val(socket_id);

    $.ajax({
        type: 'POST',
        url: '/nornir',
        data: $('form').serialize(),
        success: function(data, status, request) {
            $('#output').html(data.output).show();
            $("#submit").prop('disabled', false);
        },
        error: function() {
            $('#output').html("Unexpected error.  Try refreshing the page.").show();
        }
    });


}

