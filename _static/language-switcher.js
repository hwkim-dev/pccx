(function () {
  'use strict';

  var LANGS = {
    en: { short: 'EN', full: 'English' },
    ko: { short: 'KO', full: '한국어' }
  };

  // Match /<base>/<en|ko>/<rest> at any depth.
  // Works for both production (/pccx/en/...) and local dev (/en/...).
  function getLanguageInfo() {
    var path = window.location.pathname;
    var m = path.match(/^(.*)\/(en|ko)(\/.*|$)/);
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
    if (document.querySelector('.lang-switcher')) return;

    var langInfo = getLanguageInfo();
    if (!langInfo) return;

    var switcher = createSwitcher(langInfo);

    // PyData Sphinx Theme: navbar icon list lives in .navbar-icon-links
    // The .bd-navbar-elements .navbar-persistent--container is another option.
    var targets = [
      '.navbar-icon-links',
      '.navbar-header-items__end',
      '.bd-header-items .navbar-nav',
      '.bd-header .navbar-nav',
      'nav.bd-header',
      'header'
    ];

    for (var i = 0; i < targets.length; i++) {
      var el = document.querySelector(targets[i]);
      if (el) {
        // For icon-links list, prepend so it sits left of the icons.
        if (el.classList.contains('navbar-icon-links')) {
          el.parentNode.insertBefore(switcher, el);
        } else {
          var last = el.lastElementChild;
          el.insertBefore(switcher, last || null);
        }
        return;
      }
    }

    // Absolute fallback — pinned to top-right so it is never hidden.
    switcher.style.cssText = 'position:fixed;top:8px;right:12px;z-index:9999';
    document.body.appendChild(switcher);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectSwitcher);
  } else {
    injectSwitcher();
  }
})();
