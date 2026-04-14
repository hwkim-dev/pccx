(function () {
  'use strict';

  var LANGS = {
    en: { short: 'EN', full: 'English' },
    ko: { short: 'KO', full: '한국어' }
  };

  // Support both /xpcc/ and /pccx/ repo names
  function getLanguageInfo() {
    var path = window.location.pathname;
    var m = path.match(/^(.*\/(?:xpcc|pccx))\/(en|ko)(\/.*|$)/);
    if (!m) return null;
    return {
      current: m[2],
      base: m[1],
      rest: m[3] || '/index.html'
    };
  }

  function createSwitcher(langInfo) {
    var wrapper = document.createElement('div');
    wrapper.className = 'lang-switcher navbar-item';

    var btn = document.createElement('button');
    btn.className = 'lang-btn';
    btn.setAttribute('aria-haspopup', 'listbox');
    btn.setAttribute('aria-expanded', 'false');
    btn.setAttribute('aria-label', 'Select language');
    btn.innerHTML =
      '<span class="lang-short">' + LANGS[langInfo.current].short + '</span>' +
      '<span class="lang-arrow" aria-hidden="true">&#9662;</span>';

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

    // PyData: .navbar-header-items__end — insert before last child (theme-switcher)
    // Furo:   .sidebar-header-items__end — same approach
    var targets = [
      '.navbar-header-items__end',
      '.sidebar-header-items__end',
      '.bd-header-items .navbar-nav',
      'nav.bd-header',
      'header'
    ];

    for (var i = 0; i < targets.length; i++) {
      var el = document.querySelector(targets[i]);
      if (el) {
        var last = el.lastElementChild;
        el.insertBefore(switcher, last || null);
        return;
      }
    }

    // Absolute fallback
    switcher.style.cssText = 'position:fixed;top:8px;right:12px;z-index:9999';
    document.body.appendChild(switcher);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectSwitcher);
  } else {
    injectSwitcher();
  }
})();
