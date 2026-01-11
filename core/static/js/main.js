// ATAS - Minimal JavaScript File
document.addEventListener('DOMContentLoaded', function() {
    highlightCurrentPage();
    dismissAlerts();
});

// Auto-dismiss alerts after 5 seconds
function dismissAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.display = 'none';
        }, 5000);
    });
}
