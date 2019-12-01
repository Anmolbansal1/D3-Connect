"use strict";

function showSentRequest(result) {
    $("#add-friend-btn").html(result).attr("disabled", true);
}

function sendFriendRequest(user_id) {

    var formInput = {
        "user_b_id": user_id
    };

    $.post("/add-friend",
           formInput,
           showSentRequest
           );
}