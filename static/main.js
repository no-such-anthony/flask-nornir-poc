$(document).ready(function() {

  //click behaviour for main buttons
  $('#submit').click(function() {
      submitRun();
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

function submitRun() {
    // send ajax POST request to start background job
    $('#output').html("<h2>running...</h2>").show()
    $("#progress").html('').show();
    $("#updates li").remove();

    $.ajax({
        type: 'POST',
        url: '/nornir',
        data: $('form').serialize(),
        success: function(data, status, request) {
            $('#output').html(data.output).show();
        },
        error: function() {
            alert('Unexpected error');
        }
    });


}

function nornRun() {
    alert('run');
}
