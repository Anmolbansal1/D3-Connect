"use strict";

function acceptRequest(user_id, target_id) {
    console.log('I is - ', user_id);
    console.log(target_id);
    //$.ajax( "/friend_request", { name: "John", time: "2pm" } );
    $.ajax({
        type : 'POST',
        url : "http://localhost:5000/friend_request",
        data : { user_id: user_id, target_id: target_id, status: "accept" }
      });
    
    location.reload();
}

function rejectRequest(user_id, target_id) {
    console.log('I is - ', user_id);
    console.log(target_id);
    //$.ajax( "/friend_request", { name: "John", time: "2pm" } );
    $.ajax({
        type : 'POST',
        url : "http://localhost:5000/friend_request",
        data : { user_id: user_id, target_id: target_id, status: "reject" }
    });
    location.reload();
}