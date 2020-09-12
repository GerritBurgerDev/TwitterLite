var usernames = [];

$(document).ready(function() {
    cx = js2neo.open({host: "localhost", port: "11001", user: "neo4j", password: "lol"});
    
    var fields = [], count = 0;

    cx.run("Match (n:User) RETURN n.username", {}, {
        onRecord: function(fields) {
            count += 1;
            usernames.push(fields[0]);
        }
    });

    cx.run("Match (h:Hashtag) RETURN h.hashtag ORDER BY h.likes desc", {}, {
        onRecord: function(fields) {
            count += 1;
            usernames.push("#" + fields[0]);
        }
    });
    
    $("#autocomplete").autocomplete({
        source: usernames
    });
});