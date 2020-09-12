$(document).ready(function() {

    $(document).on('click', '.btn-like', function(event) {
        
        let mem_id = $(this).attr('mem_id');
        var tweet = $('#like-btn-'+mem_id).val();
        var likes = parseInt($('#likes-'+mem_id+'-0').text());
        var tweet_id = parseInt(tweet);

        req = $.ajax({
            data : {
                tweet : tweet_id
            },
            type: 'POST',
            url : '/like'
        }).done(function(data) {
            if (data.error) {
                if ($('#like-btn-'+mem_id).html() == ('<i class="fas fa-heart"></i> Like')) {
                    likes += 1;
                    $('#likes-'+mem_id+'-0').text(likes);
                    $('#like-btn-'+mem_id).html('<i class="fas fa-heart"></i> Unlike');
                } else {
                    likes -= 1;
                    $('#likes-'+mem_id+'-0').text(likes);
                    $('#like-btn-'+mem_id).html('<i class="fas fa-heart"></i> Like');
                }
                $('#error').text(data.error);
            } else {
                $('error').text(data.name);
            }
        });


        event.preventDefault();
    });

});