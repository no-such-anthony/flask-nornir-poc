$(document).ready(function() {

  //click behaviour for main buttons
  $('#submit').click(function() {
      submitRun();
  });

});

function submitRun() {
    // send ajax POST request to start background job
    $('#output').html("<h2>running...</h2>").show()
    $("#submit").prop('disabled', true);
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

