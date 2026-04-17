/*
 * Click-to-zoom lightbox for <img> inside content figures.
 *
 * - Attaches to every <img> within `.bd-content figure` / `.rst-content img`.
 * - Opens a full-viewport overlay with the image centered.
 * - Close with: X button, click outside image, or Esc key.
 */

(function () {
  'use strict';

  var OVERLAY_ID = 'pccx-lightbox-overlay';

  function buildOverlay() {
    var overlay = document.getElementById(OVERLAY_ID);
    if (overlay) return overlay;

    overlay = document.createElement('div');
    overlay.id = OVERLAY_ID;
    overlay.className = 'pccx-lightbox';
    overlay.innerHTML =
      '<button type="button" class="pccx-lightbox__close" aria-label="닫기">&times;</button>' +
      '<img class="pccx-lightbox__img" alt="" />';
    overlay.hidden = true;
    document.body.appendChild(overlay);

    function close() {
      overlay.hidden = true;
      overlay.classList.remove('pccx-lightbox--open');
      document.body.classList.remove('pccx-lightbox--active');
    }

    overlay.addEventListener('click', function (e) {
      // click outside image → close
      if (e.target === overlay || e.target.classList.contains('pccx-lightbox__close')) {
        close();
      }
    });

    document.addEventListener('keydown', function (e) {
      if (!overlay.hidden && e.key === 'Escape') close();
    });

    return overlay;
  }

  function open(src, alt) {
    var overlay = buildOverlay();
    var img = overlay.querySelector('.pccx-lightbox__img');
    img.src = src;
    img.alt = alt || '';
    overlay.hidden = false;
    // Force reflow for transition
    void overlay.offsetHeight;
    overlay.classList.add('pccx-lightbox--open');
    document.body.classList.add('pccx-lightbox--active');
  }

  function isZoomable(img) {
    // Skip shield badges, logos, icons — only zoom content images.
    if (img.closest('.lang-switcher')) return false;
    if (img.closest('.navbar-logo')) return false;
    if (img.closest('.navbar-icon-links')) return false;
    if (img.width && img.width < 120) return false;
    // Skip external shield.io badges
    var src = img.getAttribute('src') || '';
    if (src.indexOf('img.shields.io') !== -1) return false;
    return true;
  }

  function attach() {
    // PyData: `.bd-content` wraps article body. Fallback to common Sphinx containers.
    var roots = document.querySelectorAll('.bd-content, .rst-content, article.bd-article, main');
    var seen = new WeakSet();

    roots.forEach(function (root) {
      root.querySelectorAll('img').forEach(function (img) {
        if (seen.has(img)) return;
        if (!isZoomable(img)) return;
        seen.add(img);

        img.classList.add('pccx-zoomable');
        img.style.cursor = 'zoom-in';
        img.addEventListener('click', function (e) {
          e.preventDefault();
          open(img.getAttribute('src'), img.getAttribute('alt') || '');
        });
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', attach);
  } else {
    attach();
  }
})();
