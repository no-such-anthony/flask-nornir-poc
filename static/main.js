$(document).ready(function() {

  //click behaviour for main buttons
  $('#submit').click(function() {
      submitRun();
  });

});

function submitRun() {
    // send ajax POST request to start background job
    $('#output').html("<h2>running...</h2>").show()
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

