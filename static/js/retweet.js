$(document).ready(function() {

    $(document).on('click', '.btn-share', function(event) {
        
        let mem_id = $(this).attr('mem_id');
        var tweet = $('#share-btn-'+mem_id).val();

        req = $.ajax({
            data : {
                tweet : tweet
            },
            type: 'POST',
            url : '/share'
        })
        .done(function(data) {
            if (data.error) {
                $('#error').text(data.error);
            } else {
                $('error').text(data.name);
            }
        });


        event.preventDefault();
    });

});