(function () {
  'use strict';

  var LANGS = {
    en: { short: 'EN', full: 'English' },
    ko: { short: 'KO', full: '한국어' }
  };

  function getLanguageInfo() {
    var path = window.location.pathname;
    var enMatch = path.match(/^(.*\/xpcc)\/en(\/.*|$)/);
    var koMatch = path.match(/^(.*\/xpcc)\/ko(\/.*|$)/);
    if (enMatch) return { current: 'en', base: enMatch[1], rest: enMatch[2] || '/index.html' };
    if (koMatch) return { current: 'ko', base: koMatch[1], rest: koMatch[2] || '/index.html' };
    return null;
  }

  function createSwitcher(langInfo) {
    var wrapper = document.createElement('div');
    wrapper.className = 'lang-switcher';

    // Button: shows short code (EN / KO)
    var btn = document.createElement('button');
    btn.className = 'lang-btn';
    btn.setAttribute('aria-haspopup', 'listbox');
    btn.setAttribute('aria-expanded', 'false');
    btn.setAttribute('aria-label', 'Select language');
    btn.innerHTML =
      '<span class="lang-short">' + LANGS[langInfo.current].short + '</span>' +
      '<span class="lang-arrow" aria-hidden="true">&#9662;</span>';

    // Dropdown: shows full names
    var dropdown = document.createElement('ul');
    dropdown.className = 'lang-dropdown';
    dropdown.setAttribute('role', 'listbox');
    dropdown.hidden = true;

    Object.keys(LANGS).forEach(function (code) {
      var li = document.createElement('li');
      li.className = 'lang-option' + (code === langInfo.current ? ' lang-option--active' : '');
      li.setAttribute('role', 'option');
      li.setAttribute('aria-selected', String(code === langInfo.current));
      li.textContent = LANGS[code].full;
      li.addEventListener('click', function () {
        if (code === langInfo.current) { close(); return; }
        window.location.href = langInfo.base + '/' + code + langInfo.rest;
      });
      dropdown.appendChild(li);
    });

    function open() {
      dropdown.hidden = false;
      btn.setAttribute('aria-expanded', 'true');
      btn.classList.add('lang-btn--open');
    }
    function close() {
      dropdown.hidden = true;
      btn.setAttribute('aria-expanded', 'false');
      btn.classList.remove('lang-btn--open');
    }

    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      dropdown.hidden ? open() : close();
    });
    document.addEventListener('click', close);

    wrapper.appendChild(btn);
    wrapper.appendChild(dropdown);
    return wrapper;
  }

  function injectSwitcher() {
    var langInfo = getLanguageInfo();
    if (!langInfo) return;

    var switcher = createSwitcher(langInfo);

    // Furo: .sidebar-header-items__end holds [theme-toggle] [...] [toc-btn]
    // Insert BEFORE the last child so order becomes: theme-toggle → lang → toc-btn
    var headerEnd = document.querySelector('.sidebar-header-items__end');
    if (headerEnd) {
      var last = headerEnd.lastElementChild;
      headerEnd.insertBefore(switcher, last || null);
      return;
    }

    // Fallback
    var header = document.querySelector('header');
    if (header) { header.appendChild(switcher); return; }

    switcher.style.cssText = 'position:fixed;top:8px;right:12px;z-index:9999';
    document.body.appendChild(switcher);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectSwitcher);
  } else {
    injectSwitcher();
  }
})();
