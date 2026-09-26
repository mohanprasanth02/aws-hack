// ==========================================================================
// AQUAGUARD AI — 120 FPS / 120 HZ ULTRA-SMOOTH SCROLL ENGINE
// Powered by Lenis with hardware-accelerated momentum, RAF sub-pixel
// interpolation, scroll progress, back-to-top, and 120Hz scroll-reveal.
// ==========================================================================

(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', () => {
    initSmoothScroll();
    initScrollProgress();
    initBackToTop();
    init120HzScrollReveals();
  });

  function initSmoothScroll() {
    // If user prefers reduced motion, respect system setting
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      document.documentElement.style.scrollBehavior = 'auto';
      return;
    }

    // Never hijack scroll on the full-screen interactive Map page
    if (document.body.classList.contains('map-page-lock') || document.getElementById('map')) {
      return;
    }

    if (typeof Lenis !== 'undefined') {
      const lenis = new Lenis({
        duration: 1.15,
        easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)), // exponential ease-out for 120Hz display
        direction: 'vertical',
        gestureDirection: 'vertical',
        smooth: true,
        smoothTouch: false, // Preserve native 120Hz ProMotion on mobile touch screens
        touchMultiplier: 1.5,
        wheelMultiplier: 0.95,
        infinite: false,
        autoResize: true,
        prevent: (node) => {
          // Prevent hijacking inside map zoom, modals, tables or custom dropdowns
          return !!(
            node.closest('.leaflet-container') ||
            node.closest('.modal-body') ||
            node.closest('.dropdown-menu') ||
            node.closest('[data-lenis-prevent]')
          );
        }
      });

      window.lenis = lenis;

      // 120Hz synchronized RAF animation frame loop
      let rafId;
      function raf(time) {
        lenis.raf(time);
        rafId = requestAnimationFrame(raf);
      }
      rafId = requestAnimationFrame(raf);

      // Smooth anchor scrolling
      document.addEventListener('click', (e) => {
        const link = e.target.closest('a[href^="#"]');
        if (!link) return;
        const hash = link.getAttribute('href');
        if (hash && hash.length > 1) {
          const target = document.querySelector(hash);
          if (target) {
            e.preventDefault();
            lenis.scrollTo(target, { offset: -75, duration: 1.2 });
          }
        }
      });

      // Notify window on scroll for any dependent components
      lenis.on('scroll', (e) => {
        window.dispatchEvent(new CustomEvent('lenis-scroll', { detail: e }));
      });
    } else {
      // Fallback: Enable standard smooth scrolling in CSS
      document.documentElement.style.scrollBehavior = 'smooth';
    }
  }

  /* Glowing 120Hz scroll progress indicator across the top of the viewport */
  function initScrollProgress() {
    if (document.getElementById('aqScrollProgressBar')) return;

    const container = document.createElement('div');
    container.className = 'aq-scroll-progress-container';
    container.setAttribute('aria-hidden', 'true');

    const bar = document.createElement('div');
    bar.className = 'aq-scroll-progress-bar';
    bar.id = 'aqScrollProgressBar';
    container.appendChild(bar);
    document.body.prepend(container);

    const updateBar = (scrollRatio) => {
      const pct = Math.min(100, Math.max(0, scrollRatio * 100));
      bar.style.width = pct.toFixed(2) + '%';
    };

    if (window.lenis) {
      window.lenis.on('scroll', (e) => {
        const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
        const ratio = maxScroll > 0 ? e.scroll / maxScroll : 0;
        updateBar(ratio);
      });
    } else {
      window.addEventListener('scroll', () => {
        const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
        const ratio = maxScroll > 0 ? window.scrollY / maxScroll : 0;
        requestAnimationFrame(() => updateBar(ratio));
      }, { passive: true });
    }
  }

  /* Ultra-sleek Back to Top action button */
  function initBackToTop() {
    if (document.getElementById('aqBackToTopBtn')) return;

    const btn = document.createElement('button');
    btn.id = 'aqBackToTopBtn';
    btn.className = 'aq-back-to-top';
    btn.type = 'button';
    btn.setAttribute('aria-label', 'Return to top of page');
    btn.setAttribute('title', 'Scroll to top (120 FPS)');
    btn.innerHTML = '<i class="bi bi-chevron-up"></i>';
    document.body.appendChild(btn);

    btn.addEventListener('click', () => {
      if (window.lenis) {
        window.lenis.scrollTo(0, { duration: 1.2 });
      } else {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    });

    const toggleBtn = (scrollY) => {
      if (scrollY > 280) {
        btn.classList.add('visible');
      } else {
        btn.classList.remove('visible');
      }
    };

    if (window.lenis) {
      window.lenis.on('scroll', (e) => toggleBtn(e.scroll));
    } else {
      window.addEventListener('scroll', () => {
        requestAnimationFrame(() => toggleBtn(window.scrollY));
      }, { passive: true });
    }
  }

  /* 120Hz Hardware-accelerated Scroll Reveal Animations */
  function init120HzScrollReveals() {
    if (!('IntersectionObserver' in window)) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const targetSelectors = [
      '.glass-card',
      '.kpi-card',
      '.stat-card',
      '.chart-card',
      '.metric-box',
      '.water-balance-node',
      '.table-responsive',
      '.work-order-card',
      '.incident-card'
    ];

    const elements = document.querySelectorAll(targetSelectors.join(', '));
    if (!elements.length) return;

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed');
          observer.unobserve(entry.target);
        }
      });
    }, {
      root: null,
      threshold: 0.08,
      rootMargin: '0px 0px -40px 0px'
    });

    elements.forEach(el => {
      // Don't hide elements if already near viewport top
      const rect = el.getBoundingClientRect();
      if (rect.top < window.innerHeight * 0.85) {
        el.classList.add('scroll-reveal', 'revealed');
      } else {
        el.classList.add('scroll-reveal');
        observer.observe(el);
      }
    });
  }

  // Expose global helper to programmatically scroll smoothly
  window.aquaScrollTo = function (target, offset = -75, duration = 1.2) {
    if (window.lenis) {
      window.lenis.scrollTo(target, { offset, duration });
    } else {
      const el = typeof target === 'string' ? document.querySelector(target) : target;
      if (el) {
        const top = el.getBoundingClientRect().top + window.pageYOffset + offset;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    }
  };
})();
