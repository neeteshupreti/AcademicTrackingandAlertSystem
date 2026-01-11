/**
 * ATAS - Main JavaScript File
 * Vanilla JS for common interactions and enhancements
 */

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeAlerts();
    initializeMenuHighlight();
});

/**
 * Auto-dismiss alerts after 5 seconds
 */
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert-modern');
    alerts.forEach(alert => {
        // Add auto-close functionality
        setTimeout(() => {
            if (alert && alert.parentElement) {
                alert.style.animation = 'slideOut 0.3s ease forwards';
                setTimeout(() => {
                    alert.remove();
                }, 300);
            }
        }, 5000);
    });
}

// Slide out animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            opacity: 1;
            transform: translateY(0);
        }
        to {
            opacity: 0;
            transform: translateY(-10px);
        }
    }
`;
document.head.appendChild(style);

/**
 * Highlight current page in navigation menu
 */
function initializeMenuHighlight() {
    const currentPath = window.location.pathname;
    const menuLinks = document.querySelectorAll('.navbar-menu-link');
    
    menuLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentPath.includes(href)) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

/**
 * Smooth scroll to top
 */
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

/**
 * Format large numbers with commas
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

/**
 * Simple notification system
 */
function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    const iconMap = {
        'success': 'bi-check-circle-fill',
        'error': 'bi-exclamation-circle-fill',
        'warning': 'bi-exclamation-triangle-fill',
        'info': 'bi-info-circle-fill'
    };
    
    notification.className = `alert-modern alert-${type}`;
    notification.innerHTML = `
        <i class="bi ${iconMap[type]}"></i>
        <div>${message}</div>
        <button class="alert-close" onclick="this.parentElement.remove();">
            <i class="bi bi-x"></i>
        </button>
    `;
    
    // Insert at the top of main content
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.insertBefore(notification, mainContent.firstChild);
    }
    
    // Auto-remove notification
    if (duration > 0) {
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, duration);
    }
}

/**
 * Debounce helper for search inputs
 */
function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func(...args), delay);
    };
}

/**
 * Handle table row selection with checkboxes
 */
function initializeTableSelection() {
    const selectAllCheckbox = document.querySelector('input[name="select-all"]');
    const rowCheckboxes = document.querySelectorAll('input[name="select-row"]');
    
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            rowCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
    }
    
    rowCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const allChecked = Array.from(rowCheckboxes).every(cb => cb.checked);
            if (selectAllCheckbox) {
                selectAllCheckbox.checked = allChecked;
            }
        });
    });
}

/**
 * Smooth fade-in animation for cards
 */
function animateCardsOnLoad() {
    const cards = document.querySelectorAll('.card-modern, .stat-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(10px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.4s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 50);
    });
}

// Animate cards when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', animateCardsOnLoad);
} else {
    animateCardsOnLoad();
}

/**
 * Handle form submission feedback
 */
function handleFormSubmit(form, successMessage = 'Submitted successfully!') {
    form.addEventListener('submit', function(e) {
        // Optional: Add loading state
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Processing...';
        }
    });
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard!', 'success', 3000);
    }).catch(() => {
        showNotification('Failed to copy', 'error', 3000);
    });
}

/**
 * Export table to CSV (simplified)
 */
function exportTableToCSV(tableSelector, filename = 'export.csv') {
    const table = document.querySelector(tableSelector);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        let csvRow = [];
        cols.forEach(col => {
            csvRow.push('"' + col.innerText + '"');
        });
        csv.push(csvRow.join(','));
    });
    
    downloadFile(csv.join('\n'), filename);
}

/**
 * Download file helper
 */
function downloadFile(content, filename) {
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(content));
    element.setAttribute('download', filename);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
}

/**
 * Keyboard shortcuts
 */
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K for quick search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[type="search"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const activeModal = document.querySelector('.modal-overlay.active');
            if (activeModal) {
                activeModal.classList.remove('active');
            }
        }
    });
}

initializeKeyboardShortcuts();

/**
 * Console message for fun
 */
console.log('%c ATAS - Academic Tracking & Alert System', 'color: #3b82f6; font-size: 16px; font-weight: bold;');
console.log('%c Version 1.0 | Build with ❤️', 'color: #666; font-size: 12px;');
