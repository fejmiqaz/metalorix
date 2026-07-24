// Loader Animation
document.addEventListener('DOMContentLoaded', function() {
    anime({
        targets: '.loader-text span',
        opacity: [0, 1],
        translateY: [20, 0],
        delay: anime.stagger(100),
        easing: 'easeOutQuad',
        duration: 800
    });

    setTimeout(function() {
        document.querySelector('.loader').classList.add('hidden');

        anime({
            targets: '#welcomeTo span',
            opacity: [0, 1],
            translateY: [20, 0],
            delay: anime.stagger(50),
            easing: 'easeOutQuad',
            duration: 800
        });

        anime({
            targets: '#metalorix span',
            opacity: [0, 1],
            translateY: [30, 0],
            delay: anime.stagger(100, {start: 500}),
            easing: 'easeOutQuad',
            duration: 800
        });

        anime({
            targets: '#becomeBetter span',
            opacity: [0, 1],
            translateY: [20, 0],
            delay: anime.stagger(50, {start: 1400}),
            easing: 'easeOutQuad',
            duration: 800
        });

        anime({
            targets: '.hero-stats',
            opacity: [0, 1],
            translateY: [15, 0],
            delay: 1900,
            easing: 'easeOutQuad',
            duration: 800
        });
    }, 2500);
});

// Menu Toggle
document.getElementById('menu-toggle').addEventListener('click', function() {
    document.getElementById('sidebar').classList.toggle('open');
});

document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function() {
        document.getElementById('sidebar').classList.remove('open');
    });
});

document.addEventListener('click', function(event) {
    const sidebar = document.getElementById('sidebar');
    const menuToggle = document.getElementById('menu-toggle');

    if (!sidebar.contains(event.target) && !menuToggle.contains(event.target) && sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
    }
});

// Intersection Observer for scroll-triggered reveals
const observerOptions = { threshold: 0.2 };

function revealOnce(selector, root, onEnter) {
    const target = document.querySelector(root);
    if (!target) return;
    const observer = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                onEnter();
                obs.unobserve(entry.target);
            }
        });
    }, observerOptions);
    observer.observe(target);
}

// Philosophy section: paragraphs + growth curve
revealOnce('.philosophy-text p', '#philosophy', () => {
    document.querySelectorAll('.philosophy-text p').forEach((p, index) => {
        setTimeout(() => {
            p.style.opacity = '1';
            p.style.transform = 'translateY(0)';
        }, index * 200);
    });

    setTimeout(() => {
        const visual = document.querySelector('.philosophy-visual');
        if (visual) {
            visual.style.opacity = '1';
            visual.style.transform = 'translateY(0)';
        }
        const chart = document.querySelector('.curve-chart');
        if (chart) chart.classList.add('in-view');
    }, 500);
});

// Feed section
revealOnce('.post-item', '#feed', () => {
    document.querySelectorAll('.post-item').forEach((item, index) => {
        setTimeout(() => {
            item.style.opacity = '1';
            item.style.transform = 'translateY(0)';
        }, index * 150);
    });
});

// Shop section
revealOnce('.merch-item', '#shop', () => {
    document.querySelectorAll('.merch-item').forEach((item, index) => {
        setTimeout(() => {
            item.style.opacity = '1';
            item.style.transform = 'translateY(0)';
        }, index * 150);
    });
});