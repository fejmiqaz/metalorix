// SIDEBAR.JS
document.addEventListener('DOMContentLoaded', function () {

    const sidebar = document.getElementById('sidebar');
    const toggleButton = document.getElementById('menu-toggle'); // Assuming there's a button with this ID

    let lastScrollTop = 0;

    // Toggle sidebar visibility
    toggleButton.addEventListener('click', function () {
        sidebar.classList.toggle('open');
    });

    // Show/hide sidebar on scroll
    window.addEventListener('scroll', function () {
        let currentScroll = window.pageYOffset || document.documentElement.scrollTop;

        if (currentScroll > lastScrollTop) {
            // Scroll down
            sidebar.classList.remove('open');
        } else {
            // Scroll up
            sidebar.classList.add('open');
        }
        lastScrollTop = currentScroll <= 0 ? 0 : currentScroll; // For Mobile or negative scrolling
    });

    //ABOUT SECTION SLIDE IN
    window.addEventListener('load', function () {
        const aboutSection = document.getElementById('home');
        // aboutSection.classList.add('show');


        let welcomeTo = document.getElementById('welcomeTo');
        let metalorix = document.getElementById('metalorix');
        let becomeBetter = document.getElementById('becomeBetter');

        const elements = [metalorix, welcomeTo, becomeBetter];


        elements.forEach((element, idx) => {
            aboutSection.classList.add('show');
        })
    })
});
