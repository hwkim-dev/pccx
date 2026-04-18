/*
 * pccx — language switcher (Furo-aware).
 *
 * The static template `_templates/sidebar/brand.html` renders two anchors
 * tagged `data-pccx-lang`. This script rewrites their `href` to point at the
 * sibling-language equivalent of the current page and marks the active one.
 *
 * Path model:
 *   /pccx-FPGA-NPU-LLM-kv260/en/<rest>   ↔   /pccx-FPGA-NPU-LLM-kv260/ko/<rest>
 *
 * The regex below captures the base path dynamically, so this works at any
 * deployment prefix (including the `/<lang>/...` layout a local dev server
 * produces when serving the build output directly).
 */

(function () {
  'use strict';

  var LANG_CODES = ['en', 'ko'];

  /**
   * Parse the current path into {base, current, rest}.
   *   /pccx-FPGA-NPU-LLM-kv260/en/docs/foo.html
   *       -> { base: '/pccx-FPGA-NPU-LLM-kv260', current: 'en', rest: '/docs/foo.html' }
   *   /en/                   -> { base: '',      current: 'en', rest: '/'               }
   */
  function parsePath() {
    var path = window.location.pathname;
    var m = path.match(/^(.*)\/(en|ko)(\/.*|$)/);
    if (!m) return null;
    return {
      base:    m[1],
      current: m[2],
      rest:    m[3] || '/',
    };
  }

  function rewriteAnchors(info) {
    var anchors = document.querySelectorAll('.pccx-langswitch__btn[data-pccx-lang]');
    if (!anchors.length) return;

    anchors.forEach(function (a) {
      var code = a.getAttribute('data-pccx-lang');
      if (LANG_CODES.indexOf(code) === -1) return;

      a.href = info.base + '/' + code + info.rest;

      if (code === info.current) {
        a.classList.add('is-active');
        a.setAttribute('aria-current', 'true');
      } else {
        a.classList.remove('is-active');
        a.removeAttribute('aria-current');
      }
    });
  }

  function run() {
    var info = parsePath();
    if (!info) return;   // unknown layout (e.g. root redirect page) — leave anchors
    rewriteAnchors(info);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
})();
