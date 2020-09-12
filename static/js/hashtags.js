$(document).ready(function() {
    var regex = /#+(?:\s|$)?([A-Za-z0-9\-\.\_]*)/gi;


    $(".card-text").html(function () {
        return $(this).html().replace(regex, '<button type="submit" name="hashtag" value="$1" class="hashtag">#$1</button>');
    });

});