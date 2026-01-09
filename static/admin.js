// admin.js

async function approveVenue(requestId) {
    const response = await fetch(`/admin/venue/approve/${requestId}`, {
        method: "POST"
    });

    const result = await response.json();
    alert(result.message);
    location.reload();
}

async function rejectVenue(requestId) {
    const response = await fetch(`/admin/venue/reject/${requestId}`, {
        method: "POST"
    });

    const result = await response.json();
    alert(result.message);
    location.reload();
}

async function approveCancel(requestId) {
    const response = await fetch(`/admin/venue/cancel/approve/${requestId}`, {
        method: "POST"
    });

    const result = await response.json();
    alert(result.message);
    location.reload();
}
