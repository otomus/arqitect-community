/**
 * Arqitect — client-side search, filter, and nav logic.
 */

(function () {
  'use strict';

  /* ---- Mobile nav toggle ---- */
  document.addEventListener('DOMContentLoaded', function () {
    var toggle = document.querySelector('.nav-toggle');
    var links = document.querySelector('.nav-links');
    if (toggle && links) {
      toggle.addEventListener('click', function () {
        links.classList.toggle('open');
      });
    }

    initSearch();
    initFilter();
    highlightActiveNav();
    initScrollReveal();
    initParticles();
    initStatCounters();
  });

  /** Highlight current page in nav */
  function highlightActiveNav() {
    var path = window.location.pathname;
    var navLinks = document.querySelectorAll('.nav-links a');
    navLinks.forEach(function (link) {
      var href = link.getAttribute('href');
      if (!href) return;
      /* Resolve relative href for comparison */
      var linkPath = new URL(href, window.location.origin + window.location.pathname).pathname;
      if (path === linkPath || (path.endsWith('/') && linkPath === path + 'index.html')) {
        link.classList.add('active');
      }
    });
  }

  /** Search cards by text */
  function initSearch() {
    var input = document.querySelector('.search-input');
    if (!input) return;

    input.addEventListener('input', filterCards);
  }

  /** Filter by select dropdown */
  function initFilter() {
    var selects = document.querySelectorAll('.filter-select');
    selects.forEach(function (sel) {
      sel.addEventListener('change', filterCards);
    });
  }

  /** Combined search + filter logic */
  function filterCards() {
    var input = document.querySelector('.search-input');
    var select = document.querySelector('.filter-select');
    var cards = document.querySelectorAll('.card[data-search]');
    var countEl = document.querySelector('.result-count');

    var query = input ? input.value.toLowerCase().trim() : '';
    var filter = select ? select.value.toLowerCase() : '';
    var visible = 0;

    cards.forEach(function (card) {
      var text = (card.getAttribute('data-search') || '').toLowerCase();
      var tags = (card.getAttribute('data-tags') || '').toLowerCase();
      var category = (card.getAttribute('data-category') || '').toLowerCase();

      var matchesQuery = !query || text.indexOf(query) !== -1;
      var matchesFilter = !filter || tags.indexOf(filter) !== -1 || category === filter;

      if (matchesQuery && matchesFilter) {
        card.style.display = '';
        visible++;
      } else {
        card.style.display = 'none';
      }
    });

    if (countEl) {
      countEl.textContent = visible + ' result' + (visible !== 1 ? 's' : '');
    }
  }
  /** Scroll-triggered reveal animations */
  function initScrollReveal() {
    var targets = document.querySelectorAll(
      '.vision-pillar, .dream, .stat-item, .step, .type-card, .reveal'
    );
    if (!targets.length) return;

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });

    targets.forEach(function (el) {
      observer.observe(el);
    });
  }

  /** Floating particle background */
  function initParticles() {
    var container = document.createElement('div');
    container.className = 'particles';
    document.body.appendChild(container);

    var PARTICLE_COUNT = 30;

    for (var i = 0; i < PARTICLE_COUNT; i++) {
      createParticle(container, true);
    }
  }

  function createParticle(container, randomStart) {
    var particle = document.createElement('div');
    particle.className = 'particle';

    var size = Math.random() * 2 + 1;
    var duration = Math.random() * 12 + 10;
    var left = Math.random() * 100;
    var delay = randomStart ? Math.random() * -duration : 0;
    var hue = Math.random() > 0.5 ? '180, 100%, 50%' : '155, 100%, 50%';

    particle.style.width = size + 'px';
    particle.style.height = size + 'px';
    particle.style.left = left + '%';
    particle.style.background = 'hsl(' + hue + ')';
    particle.style.boxShadow = '0 0 ' + (size * 3) + 'px hsl(' + hue + ')';
    particle.style.animationDuration = duration + 's';
    particle.style.animationDelay = delay + 's';

    container.appendChild(particle);

    particle.addEventListener('animationiteration', function () {
      particle.style.left = Math.random() * 100 + '%';
    });
  }

  /** Animate stat numbers counting up */
  function initStatCounters() {
    var statNumbers = document.querySelectorAll('.stat-number');
    if (!statNumbers.length) return;

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          animateCount(entry.target);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });

    statNumbers.forEach(function (el) {
      observer.observe(el);
    });
  }

  function animateCount(el) {
    var target = parseInt(el.textContent, 10);
    if (isNaN(target)) return;

    var duration = 1500;
    var startTime = null;
    el.textContent = '0';

    function step(timestamp) {
      if (!startTime) startTime = timestamp;
      var progress = Math.min((timestamp - startTime) / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.floor(eased * target);
      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        el.textContent = target;
      }
    }

    requestAnimationFrame(step);
  }

})();
