$(document).ready(function() {

    $(document).on('click', '.btn-post', function(event) {
        
        var tweet = $('#message').val();

        req = $.ajax({
            data : {
                tweet : tweet
            },
            type: 'POST',
            url : '/post'
        }).done(function(data) {
            if (data.error) {
                $('#message').val('');
                $('#error').text(data.error);
            } else {
                $('error').text(data.name);
            }
        });


        event.preventDefault();
    });

});