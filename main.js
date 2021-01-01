$(document).ready(function() {

  //click behaviour for main buttons
  $('#nornInv').click(function() {
      nornInv();
  });

  $('#nornRun').click(function() {
      nornRun();
  });

});

function nornInv() {
    // send ajax POST request to start background job
    $.ajax({
        type: 'POST',
        url: '/inv',
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
