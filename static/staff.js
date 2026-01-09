// staff.js

// Venue Booking
const venueForm = document.getElementById("venueForm");

if (venueForm) {
    venueForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        const formData = new FormData(venueForm);

        const response = await fetch("/staff/venue/book", {
            method: "POST",
            body: formData
        });

        const result = await response.json();
        alert(result.message);
        venueForm.reset();
    });
}

// Cancel Venue Request
async function cancelVenue(requestId) {
    if (!confirm("Are you sure you want to cancel this booking?")) return;

    const response = await fetch(`/staff/venue/cancel/${requestId}`, {
        method: "POST"
    });

    const result = await response.json();
    alert(result.message);
    location.reload();
}
