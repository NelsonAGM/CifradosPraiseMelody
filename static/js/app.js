// Main Application JavaScript for Worship Songs App

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    setupDarkMode();
    setupFormValidation();
    setupSearchFunctionality();
    setupKeyboardShortcuts();
    
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

/**
 * Setup dark mode functionality
 */
function setupDarkMode() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    const body = document.body;
    
    // Check for saved dark mode preference or default to 'light'
    const currentMode = localStorage.getItem('darkMode') || 'light';
    
    if (currentMode === 'dark') {
        body.classList.add('dark-mode');
        updateDarkModeToggle(true);
    }
    
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function() {
            body.classList.toggle('dark-mode');
            const isDarkMode = body.classList.contains('dark-mode');
            
            // Save preference
            localStorage.setItem('darkMode', isDarkMode ? 'dark' : 'light');
            updateDarkModeToggle(isDarkMode);
        });
    }
}

/**
 * Update dark mode toggle button
 */
function updateDarkModeToggle(isDarkMode) {
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        const icon = darkModeToggle.querySelector('i');
        const text = darkModeToggle.querySelector('.d-none.d-sm-inline') || darkModeToggle;
        
        if (isDarkMode) {
            icon.className = 'fas fa-sun me-1';
            if (text.textContent) {
                text.textContent = ' Light Mode';
            }
        } else {
            icon.className = 'fas fa-moon me-1';
            if (text.textContent) {
                text.textContent = ' Dark Mode';
            }
        }
    }
}

/**
 * Setup form validation
 */
function setupFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * Setup search functionality with debouncing
 */
function setupSearchFunctionality() {
    const searchInput = document.getElementById('search');
    if (!searchInput) return;
    
    let searchTimeout;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        
        searchTimeout = setTimeout(function() {
            // Auto-submit search form after user stops typing
            const form = searchInput.closest('form');
            if (form) {
                form.submit();
            }
        }, 500); // Wait 500ms after user stops typing
    });
}

/**
 * Setup keyboard shortcuts
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Only trigger shortcuts when not in form inputs
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
            return;
        }
        
        switch(e.key) {
            case 'n':
            case 'N':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    window.location.href = '/add';
                }
                break;
            case 'h':
            case 'H':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    window.location.href = '/';
                }
                break;
            case 'd':
            case 'D':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    const darkModeToggle = document.getElementById('darkModeToggle');
                    if (darkModeToggle) {
                        darkModeToggle.click();
                    }
                }
                break;
        }
    });
}

/**
 * Show loading state on buttons
 */
function showLoading(button) {
    if (!button) return;
    
    button.disabled = true;
    button.classList.add('loading');
    
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Loading...';
    
    // Store original text for later restoration
    button.dataset.originalText = originalText;
}

/**
 * Hide loading state on buttons
 */
function hideLoading(button) {
    if (!button) return;
    
    button.disabled = false;
    button.classList.remove('loading');
    
    if (button.dataset.originalText) {
        button.innerHTML = button.dataset.originalText;
        delete button.dataset.originalText;
    }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1080';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Initialize and show toast
    const toastElement = document.getElementById(toastId);
    if (typeof bootstrap !== 'undefined') {
        const toast = new bootstrap.Toast(toastElement, {
            autohide: true,
            delay: 5000
        });
        toast.show();
        
        // Remove toast element after it's hidden
        toastElement.addEventListener('hidden.bs.toast', function() {
            toastElement.remove();
        });
    }
}

/**
 * Confirm action with user
 */
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

/**
 * Copy text to clipboard
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('Copied to clipboard!', 'success');
    } catch (err) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        
        try {
            document.execCommand('copy');
            showToast('Copied to clipboard!', 'success');
        } catch (err) {
            showToast('Failed to copy to clipboard', 'danger');
        }
        
        document.body.removeChild(textArea);
    }
}

/**
 * Debounce function to limit API calls
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        
        if (callNow) func.apply(context, args);
    };
}

/**
 * Validate audio file
 */
function validateAudioFile(file) {
    const allowedTypes = ['audio/mp3', 'audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp4'];
    const maxSize = 50 * 1024 * 1024; // 50MB
    
    if (!allowedTypes.includes(file.type)) {
        showToast('Please select a valid audio file (MP3, WAV, OGG, M4A)', 'danger');
        return false;
    }
    
    if (file.size > maxSize) {
        showToast('File size must be less than 50MB', 'danger');
        return false;
    }
    
    return true;
}

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Handle file input changes
 */
function setupFileInputHandling() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                // Show file info
                const fileInfo = document.createElement('div');
                fileInfo.className = 'file-info mt-2 text-muted small';
                fileInfo.innerHTML = `
                    <i class="fas fa-file-audio me-1"></i>
                    ${file.name} (${formatFileSize(file.size)})
                `;
                
                // Remove existing file info
                const existingInfo = input.parentNode.querySelector('.file-info');
                if (existingInfo) {
                    existingInfo.remove();
                }
                
                // Add new file info
                input.parentNode.appendChild(fileInfo);
                
                // Validate file
                if (input.accept && input.accept.includes('audio')) {
                    validateAudioFile(file);
                }
            }
        });
    });
}

// Initialize file input handling when DOM is ready
document.addEventListener('DOMContentLoaded', setupFileInputHandling);

// Global utility functions
window.AppUtils = {
    showLoading,
    hideLoading,
    showToast,
    confirmAction,
    copyToClipboard,
    debounce,
    validateAudioFile,
    formatFileSize
};
