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
})();
