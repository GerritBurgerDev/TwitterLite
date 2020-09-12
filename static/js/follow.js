$(document).ready(function() {

    $(document).on('click', '.follow-btn', function(event) {
        
        let mem_id = $(this).attr('mem_id');
        var name = $('#follow-btn'+mem_id).val();

        var get_int = parseInt($("#following").text());

        req = $.ajax({
            data : {
                name : name
            },
            type: 'POST',
            url : '/follow'
        })
        .done(function(data) {
            if (data.error) {
                get_int = get_int + 1;
                $("#following").text(get_int);
                $(".suggestion-"+mem_id).hide('slow');
                $('#error').text(data.error);
            } else {
                $('error').text(data.name);
            }
        });


        event.preventDefault();
    });

});

$(document).ready(function() {

    $(document).on('click', '.follow-btn-users', function(event) {
        
        let mem_id = $(this).attr('mem_id');
        var name = $('#follow-btn'+mem_id).val();

        req = $.ajax({
            data : {
                name : name
            },
            type: 'POST',
            url : '/follow'
        })
        .done(function(data) {
            if (data.error) {
                get_int = get_int + 1;
                $(".suggestion-"+mem_id).hide('slow');
                $('#error').text(data.error);
            } else {
                $('error').text(data.name);
            }
        });


        event.preventDefault();
    });

});


$(document).ready(function() {

    $(document).on('click', '.follow-btn-user', function(event) {
        
        var name = $('#follow-user').val();
        var get_int = parseInt($("#followers").text());

        req = $.ajax({
            data : {
                name : name
            },
            type: 'POST',
            url : '/follow'
        })
        .done(function(data) {
            if (data.error) {
                if ($('.disabled')[0]) {
                } else {
                    get_int = get_int + 1;
                    $("#followers").text(get_int);
                    document.getElementById('follow-user').disabled = true;
                    $('#error').text(data.error);
                }
                
            } else {
                $('error').text(data.name);
            }
        });


        event.preventDefault();
    });

});