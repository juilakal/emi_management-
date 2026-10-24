/**
 * EMI Management System - Core JavaScript
 * Handles sidebar toggling, flash dismissal, and modal helpers.
 */

document.addEventListener("DOMContentLoaded", () => {
    // 1. Mobile Sidebar Toggle
    const sidebarToggle = document.getElementById("sidebarToggle");
    const sidebar = document.querySelector(".app-sidebar");
    const backdrop = document.getElementById("sidebarBackdrop");

    if (sidebarToggle && sidebar && backdrop) {
        sidebarToggle.addEventListener("click", () => {
            sidebar.classList.toggle("show");
            backdrop.classList.toggle("show");
        });

        backdrop.addEventListener("click", () => {
            sidebar.classList.remove("show");
            backdrop.classList.remove("show");
        });
    }

    // 2. Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll(".alert-dismissible");
    alerts.forEach((alert) => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });

    // 3. Prevent duplicate form submissions on button click
    const forms = document.querySelectorAll("form:not(.no-disable-btn)");
    forms.forEach((form) => {
        form.addEventListener("submit", (e) => {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !form.checkValidity || (form.checkValidity && form.checkValidity())) {
                submitBtn.disabled = true;
                const origText = submitBtn.innerHTML;
                submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Processing...`;
                // Re-enable after 8 seconds in case response is download or validation failed on client
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = origText;
                }, 8000);
            }
        });
    });
});
