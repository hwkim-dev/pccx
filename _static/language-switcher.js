(function () {
  'use strict';

  function getLanguageInfo() {
    var path = window.location.pathname;
    var enMatch = path.match(/^(.*\/xpcc)\/en(\/.*|$)/);
    var koMatch = path.match(/^(.*\/xpcc)\/ko(\/.*|$)/);

    if (enMatch) {
      return { current: 'en', base: enMatch[1], rest: enMatch[2] || '/index.html' };
    }
    if (koMatch) {
      return { current: 'ko', base: koMatch[1], rest: koMatch[2] || '/index.html' };
    }
    return null;
  }

  function createSwitcher(langInfo) {
    var wrapper = document.createElement('div');
    wrapper.className = 'lang-switcher';

    var globe = document.createElement('span');
    globe.className = 'lang-globe';
    globe.textContent = '\uD83C\uDF10';
    globe.setAttribute('aria-hidden', 'true');

    var select = document.createElement('select');
    select.className = 'lang-select';
    select.setAttribute('aria-label', 'Select language / 언어 선택');

    var langs = [
      { value: 'en', label: 'English' },
      { value: 'ko', label: '\ud55c\uad6d\uc5b4' }
    ];

    langs.forEach(function (l) {
      var opt = document.createElement('option');
      opt.value = l.value;
      opt.textContent = l.label;
      if (l.value === langInfo.current) opt.selected = true;
      select.appendChild(opt);
    });

    select.addEventListener('change', function () {
      var newLang = this.value;
      var newUrl = langInfo.base + '/' + newLang + langInfo.rest;
      window.location.href = newUrl;
    });

    wrapper.appendChild(globe);
    wrapper.appendChild(select);
    return wrapper;
  }

  function injectSwitcher() {
    var langInfo = getLanguageInfo();
    if (!langInfo) return;

    var switcher = createSwitcher(langInfo);

    // Furo sidebar header is the ideal location
    var targets = [
      '.sidebar-header-items__end',
      '.sidebar-header-items',
      '.sidebar-header',
      '.header-items__end',
      'header'
    ];

    for (var i = 0; i < targets.length; i++) {
      var el = document.querySelector(targets[i]);
      if (el) {
        el.appendChild(switcher);
        return;
      }
    }

    // Absolute fallback: fixed top-right corner
    switcher.style.position = 'fixed';
    switcher.style.top = '8px';
    switcher.style.right = '12px';
    switcher.style.zIndex = '9999';
    document.body.appendChild(switcher);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectSwitcher);
  } else {
    injectSwitcher();
  }
})();
