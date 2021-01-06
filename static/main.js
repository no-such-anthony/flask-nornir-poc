$(document).ready(function() {

    //click behaviour for main buttons
    $('#submit').click(function() {
        submitRun();
    });

    // Hook up ACE editor to all textareas with data-editor attribute
    $(function () {
        $('textarea[data-editor]').each(function () {
            var textarea = $(this);
            var mode = textarea.data('editor');

            var editDiv = $('<div>', {
                position: 'absolute',
                width: textarea.width(),
                height: textarea.height(),
                'class': textarea.attr('class')
            }).insertBefore(textarea);

            textarea.css('visibility', 'hidden');
            textarea.css('width', '0');
            textarea.css('height', '0');

            var editor = ace.edit(editDiv[0]);
            editor.renderer.setShowGutter(false);
            editor.getSession().setValue(textarea.val());
            editor.getSession().setMode("ace/mode/" + mode);
            editor.setTheme("ace/theme/twilight");

            // copy back to textarea on form submit...
            $('#submit').mousedown(function () {
                textarea.val(editor.getSession().getValue());
            })

        });
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

