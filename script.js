// sidebar.js

document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');

    sidebar.addEventListener('mouseover', function() {
        sidebar.style.transform = 'translateX(0)';
    });

    sidebar.addEventListener('mouseleave', function() {
        sidebar.style.transform = 'translateX(-75%)';
    });
    // Handle touch events for mobile
    sidebar.addEventListener('touchstart', function() {
        sidebar.style.transform = 'translateX(0)';
    });

    document.addEventListener('touchend', function(event) {
        if (!sidebar.contains(event.target)) {
            sidebar.style.transform = 'translateX(-75%)';
        }
    });
});
