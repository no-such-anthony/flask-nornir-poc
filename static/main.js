$(document).ready(function() {

  //click behaviour for main buttons
  $('#submit').click(function() {
      submitRun();
  });

});

function submitRun() {
    // send ajax POST request to start background job
    $('#output').html("<h2>running...</h2>").show()
    $("#progress").html('').show();
    $("#updates li").remove();

    startPoll();
    $.ajax({
        type: 'POST',
        url: '/nornir',
        data: $('form').serialize(),
        success: function(data, status, request) {
            $('#output').html(data.output).show();
            stopPoll();
            poll();
        },
        error: function() {
            alert('Unexpected error');
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

