// Loader Animation
document.addEventListener('DOMContentLoaded', function() {
    // Animate loader text
    anime({
        targets: '.loader-text span',
        opacity: [0, 1],
        translateY: [20, 0],
        delay: anime.stagger(100),
        easing: 'easeOutQuad',
        duration: 800
    });

    // Hide loader after animations complete
    setTimeout(function() {
        document.querySelector('.loader').classList.add('hidden');

        // Animate shapes
        anime({
            targets: '.shape',
            opacity: [0, 0.3],
            delay: anime.stagger(200),
            duration: 1500,
            easing: 'easeOutQuad'
        });

        // Animate welcome text
        anime({
            targets: '#welcomeTo span',
            opacity: [0, 1],
            translateY: [20, 0],
            delay: anime.stagger(50),
            easing: 'easeOutQuad',
            duration: 800
        });

        // Animate brand name
        anime({
            targets: '#metalorix span',
            opacity: [0, 1],
            translateY: [30, 0],
            delay: anime.stagger(100, {start: 500}),
            easing: 'easeOutQuad',
            duration: 800
        });

        // Animate motto text
        anime({
            targets: '#becomeBetter span',
            opacity: [0, 1],
            translateY: [20, 0],
            delay: anime.stagger(50, {start: 1400}),
            easing: 'easeOutQuad',
            duration: 800
        });
    }, 2500);
});

// Custom Cursor
document.addEventListener('mousemove', function(e) {
    const cursor = document.querySelector('.cursor');
    const cursorFollower = document.querySelector('.cursor-follower');

    // Show cursors after first mouse movement
    if (cursor.style.opacity === '') {
        cursor.style.opacity = '1';
        cursorFollower.style.opacity = '1';
    }

    cursor.style.left = e.clientX + 'px';
    cursor.style.top = e.clientY + 'px';

    setTimeout(function() {
        cursorFollower.style.left = e.clientX + 'px';
        cursorFollower.style.top = e.clientY + 'px';
    }, 50);
});

// Cursor hover effect on interactive elements
document.querySelectorAll('a, button').forEach(item => {
    item.addEventListener('mouseenter', function() {
        document.querySelector('.cursor').classList.add('active');
        document.querySelector('.cursor-follower').classList.add('active');
    });

    item.addEventListener('mouseleave', function() {
        document.querySelector('.cursor').classList.remove('active');
        document.querySelector('.cursor-follower').classList.remove('active');
    });
});

// Menu Toggle
document.getElementById('menu-toggle').addEventListener('click', function() {
    document.getElementById('sidebar').classList.toggle('open');
});

// Close sidebar when clicking a nav link
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function() {
        document.getElementById('sidebar').classList.remove('open');
    });
});

// Close sidebar when clicking outside
document.addEventListener('click', function(event) {
    const sidebar = document.getElementById('sidebar');
    const menuToggle = document.getElementById('menu-toggle');

    if (!sidebar.contains(event.target) && !menuToggle.contains(event.target) && sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
    }
});

// Intersection Observer for section animations
const observerOptions = {
    threshold: 0.2
};

// Observer for About section
const aboutObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            // Animate text paragraphs
            document.querySelectorAll('.about-text p').forEach((p, index) => {
                setTimeout(() => {
                    p.style.opacity = '1';
                    p.style.transform = 'translateY(0)';
                }, index * 200);
            });

            // Animate visual element
            setTimeout(() => {
                document.querySelector('.visual-element').style.opacity = '1';
                document.querySelector('.visual-element').style.transform = 'translateY(0)';

                // Animate progress ring
                const circle = document.querySelector('.progress-ring-circle');
                // 565.48 is the circumference of a circle with radius 90
                // 1% progress means 99% of the circle should be hidden
                const offset = 565.48 - (1 / 100 * 565.48);
                setTimeout(() => {
                    circle.style.strokeDashoffset = offset;
                }, 200);
            }, 600);

            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

// Observer for Posts section
const postsObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            document.querySelectorAll('.post-item').forEach((item, index) => {
                setTimeout(() => {
                    item.style.opacity = '1';
                    item.style.transform = 'translateY(0)';
                }, index * 200);
            });
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

// Observer for Merchandise section
const merchObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            document.querySelectorAll('.merch-item').forEach((item, index) => {
                setTimeout(() => {
                    item.style.opacity = '1';
                    item.style.transform = 'translateY(0)';
                }, index * 200);
            });
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

// Start observing sections
document.addEventListener('DOMContentLoaded', function() {
    aboutObserver.observe(document.querySelector('#about'));
    postsObserver.observe(document.querySelector('#posts'));
    merchObserver.observe(document.querySelector('#merchandise'));
});
