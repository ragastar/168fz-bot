// ========================================
// 168-ФЗ Landing — Interactions
// ========================================

(function () {
    'use strict';

    // Navbar scroll effect
    const navbar = document.getElementById('navbar');
    let lastScroll = 0;

    window.addEventListener('scroll', () => {
        const scroll = window.scrollY;
        navbar.classList.toggle('navbar--scrolled', scroll > 60);
        lastScroll = scroll;
    }, { passive: true });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const offset = navbar.offsetHeight + 16;
                const top = target.getBoundingClientRect().top + window.scrollY - offset;
                window.scrollTo({ top, behavior: 'smooth' });
            }
        });
    });

    // Intersection Observer for scroll animations
    const observerOptions = {
        threshold: 0.15,
        rootMargin: '0px 0px -40px 0px'
    };

    const animObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const delay = parseInt(entry.target.dataset.delay) || 0;
                setTimeout(() => {
                    entry.target.classList.add('visible');
                }, delay);
                animObserver.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe all animated elements
    document.querySelectorAll('.anim-fade').forEach(el => {
        animObserver.observe(el);
    });

    // Demo card items animation (slide in from right)
    const demoObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const delay = parseInt(entry.target.dataset.delay) || 0;
                setTimeout(() => {
                    entry.target.classList.add('visible');
                }, delay);
                demoObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('[data-anim="slide-in"]').forEach(el => {
        demoObserver.observe(el);
    });

    // FAQ smooth toggle animation
    document.querySelectorAll('.faq-item').forEach(item => {
        const summary = item.querySelector('summary');
        const answer = item.querySelector('.faq-item__answer');

        summary.addEventListener('click', (e) => {
            e.preventDefault();

            if (item.open) {
                answer.style.maxHeight = answer.scrollHeight + 'px';
                requestAnimationFrame(() => {
                    answer.style.maxHeight = '0';
                    answer.style.opacity = '0';
                });
                setTimeout(() => {
                    item.open = false;
                    answer.style.maxHeight = '';
                    answer.style.opacity = '';
                }, 300);
            } else {
                item.open = true;
                const height = answer.scrollHeight;
                answer.style.maxHeight = '0';
                answer.style.opacity = '0';
                requestAnimationFrame(() => {
                    answer.style.maxHeight = height + 'px';
                    answer.style.opacity = '1';
                });
                setTimeout(() => {
                    answer.style.maxHeight = '';
                    answer.style.opacity = '';
                }, 300);
            }
        });
    });

    // Add transition styles for FAQ answers
    const style = document.createElement('style');
    style.textContent = `.faq-item__answer { overflow: hidden; transition: max-height 0.3s ease, opacity 0.3s ease; }`;
    document.head.appendChild(style);

})();
