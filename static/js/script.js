// Handle form toggle on the Dashboard page
document.addEventListener("DOMContentLoaded", () => {
    const registerBtn = document.querySelector(".btn[href='#register']");
    const loginBtn = document.querySelector(".btn[href='#login']");
    const registerForm = document.querySelector("#register");
    const loginForm = document.querySelector("#login");

    if (registerBtn && loginBtn) {
        registerBtn.addEventListener("click", (e) => {
            e.preventDefault();
            loginForm.classList.add("hidden");
            registerForm.classList.remove("hidden");
        });

        loginBtn.addEventListener("click", (e) => {
            e.preventDefault();
            registerForm.classList.add("hidden");
            loginForm.classList.remove("hidden");
        });
    }
});

// Timer logic for reservation
function startReservationTimer(duration, displayElement) {
    let timer = duration, minutes, seconds;
    const interval = setInterval(() => {
        minutes = Math.floor(timer / 60);
        seconds = timer % 60;

        displayElement.textContent = `${minutes}:${seconds < 10 ? "0" : ""}${seconds}`;

        if (--timer < 0) {
            clearInterval(interval);
            displayElement.textContent = "Reservation Expired!";
            alert("Your reservation has expired. Please try again.");
            window.location.reload(); // Reload to show slots as available again
        }
    }, 1000);
}

// Start reservation timer if it's on the slots page
document.addEventListener("DOMContentLoaded", () => {
    const timerElement = document.getElementById("reservation-timer");
    if (timerElement) {
        const reservationDuration = 10 * 60; // 10 minutes in seconds
        startReservationTimer(reservationDuration, timerElement);
    }
});

// Parking timer starts when the camera recognizes the license plate
function startParkingTimer() {
    const timerElement = document.getElementById("parking-timer");
    let startTime = Date.now();

    const interval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;

        timerElement.textContent = `${minutes}:${seconds < 10 ? "0" : ""}${seconds}`;
    }, 1000);

    return interval; // Return the interval ID to stop the timer later
}

// Stop parking timer and redirect to payment
function stopParkingTimer(intervalId) {
    clearInterval(intervalId);
    alert("Parking session ended. Redirecting to payment...");
    window.location.href = "/payment"; // Redirect to payment page
}
