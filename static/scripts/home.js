document.addEventListener('DOMContentLoaded', function () {
  const carousel = document.getElementById('trackCarousel');
  if (!carousel) return;

  const items = Array.from(carousel.querySelectorAll('.box'));
  if (items.length === 0) return;

  const wrapPrev = document.querySelector('.carousel-btn-wrap.prev');
  const wrapNext = document.querySelector('.carousel-btn-wrap.next');

  const btnPrev = document.querySelector('.carousel-btn.prev');
  const btnNext = document.querySelector('.carousel-btn.next');

  function centerItem(el, behaviour = 'smooth') {
    const left = el.offsetLeft - (carousel.clientWidth - el.clientWidth) / 2;
    carousel.scrollTo({ left, behavior: behaviour });
  }

  /* Insert start/finish markers into the carousel */
  function insertImgLineMarkers(carousel) {
    if (!carousel) return;

    if (carousel.querySelector('.line-marker.start') || carousel.querySelector('.line-marker.finish')) return;

    function makeMarker(name, src, alt) {
      const wrapper = document.createElement('div');
      wrapper.className = `line-marker ${name}`;
      wrapper.setAttribute('aria-hidden', 'true');

      const img = document.createElement('img');
      img.src = src;
      img.alt = alt || '';
      img.loading = 'lazy';

      img.style.visibility = 'hidden';
      img.style.display = 'block';

      wrapper.appendChild(img);
      return wrapper;
    }

    const startMarker = makeMarker('start', '/static/images/line-start.jpg', 'Start line');
    const finishMarker = makeMarker('finish', '/static/images/line-finish.jpg', 'Finish line');

    const firstChild = carousel.firstElementChild;
    if (firstChild) carousel.insertBefore(startMarker, firstChild);
    carousel.appendChild(finishMarker);

    function updateMarkerHeights() {
      const h = Math.max(0, carousel.clientHeight);
      if (h <= 0) return;
      const imgs = carousel.querySelectorAll('.line-marker img');
      imgs.forEach(img => {
        img.style.height = `${h}px`;
        img.style.width = 'auto';
        img.style.visibility = 'visible';
      });
    }

    const imgs = carousel.querySelectorAll('.line-marker img');
    imgs.forEach(img => {
      if (img.complete) {
        updateMarkerHeights();
      } else {
        img.addEventListener('load', updateMarkerHeights, { once: true });
      }
    });

    let ro;
    if (window.ResizeObserver) {
      ro = new ResizeObserver(() => {
        updateMarkerHeights();
      });
      ro.observe(carousel);
    }

    window.addEventListener('resize', () => {
      clearTimeout(window.__lineMarkerResizeTimer);
      window.__lineMarkerResizeTimer = setTimeout(updateMarkerHeights, 80);
    });
  }

  insertImgLineMarkers(carousel);

  function applyFlagBackgrounds() {
    const serverEl = document.getElementById('server-data');
    if (!serverEl) return;
    let server;
    try {
      server = JSON.parse(serverEl.textContent || '{}');
    } catch (err) {
      return;
    }
    const tracks = server.tracks || [];
    const boxes = Array.from(carousel.querySelectorAll('.box'));

    boxes.forEach(box => {
      const attr = box.getAttribute('data-detailed-flag') || '';
      const idx = parseInt(box.getAttribute('data-index'), 10);
      const fallbackTrack = (typeof idx === 'number' && tracks[idx]) ? tracks[idx] : null;
      const filename = attr || (fallbackTrack && fallbackTrack.detailed_flag) || '';

      if (filename) {
        const url = '/static/images/textured-flags/' + encodeURIComponent(filename);
        const gradient = 'linear-gradient(135deg, rgba(24,24,24,0.72) 0%, rgba(30,27,27,0.48) 50%, rgba(19,14,14,0.58) 100%)';
        box.style.backgroundImage = `${gradient}, url("${url}")`;
        box.classList.add('has-detailed-bg');
      } else {
        box.classList.remove('has-detailed-bg');
      }
    });
  }

  applyFlagBackgrounds();

  function setActiveNearest() {
    const center = carousel.scrollLeft + carousel.clientWidth / 2;
    let nearest = null;
    let minDist = Infinity;

    const currentItems = Array.from(carousel.querySelectorAll('.box'));
    currentItems.forEach(item => {
      const itemCenter = item.offsetLeft + item.offsetWidth / 2;
      const dist = Math.abs(center - itemCenter);
      if (dist < minDist) {
        minDist = dist;
        nearest = item;
      }
    });

    currentItems.forEach(i => i.classList.toggle('active', i === nearest));

    const quickpickArrow = document.getElementById('quickpick-arrow');
    const quickpickItems = Array.from(document.querySelectorAll('.quickpick-item'));

    function updateArrow() {
      const active = carousel.querySelector('.box.active');
      if (!active) return;

      const idx = currentItems.indexOf(active);
      if (idx === -1 || !quickpickItems[idx]) return;

      const target = quickpickItems[idx];
      const rect = target.getBoundingClientRect();
      const barRect = document.querySelector('.quickpick-bar').getBoundingClientRect();

      const centerPos = rect.left + rect.width / 2 - barRect.left;
      quickpickArrow.style.left = `${centerPos - 8}px`;
    }

    updateArrow();
    window.addEventListener('resize', updateArrow);
  }

  function updateArrowsVisibility() {
    if (!wrapPrev || !wrapNext) return;

    const scLeft = Math.max(0, carousel.scrollLeft);
    const maxScroll = Math.max(0, carousel.scrollWidth - carousel.clientWidth);
    const epsilon = 6;

    if (scLeft <= epsilon) {
      wrapPrev.classList.add('hidden');
      wrapPrev.setAttribute('aria-hidden', 'true');
    } else {
      wrapPrev.classList.remove('hidden');
      wrapPrev.removeAttribute('aria-hidden');
    }

    if (scLeft >= (maxScroll - epsilon)) {
      wrapNext.classList.add('hidden');
      wrapNext.setAttribute('aria-hidden', 'true');
    } else {
      wrapNext.classList.remove('hidden');
      wrapNext.removeAttribute('aria-hidden');
    }
  }

  let scrollTimer = null;
  carousel.addEventListener('scroll', function () {
    setActiveNearest();
    updateArrowsVisibility();
    if (scrollTimer) clearTimeout(scrollTimer);
    scrollTimer = setTimeout(() => {
      setActiveNearest();
      updateArrowsVisibility();
    }, 110);
  });

  window.addEventListener('resize', () => {
    setActiveNearest();
    updateArrowsVisibility();
  });

  function indexOfActive() {
    return items.findIndex(i => i.classList.contains('active'));
  }

  if (btnPrev) btnPrev.addEventListener('click', function () {
    if (wrapPrev && wrapPrev.classList.contains('hidden')) return;
    let idx = indexOfActive();
    if (idx <= 0) idx = 0;
    else idx = idx - 1;
    if (items[idx]) centerItem(items[idx]);
  });

  if (btnNext) btnNext.addEventListener('click', function () {
    if (wrapNext && wrapNext.classList.contains('hidden')) return;
    let idx = indexOfActive();
    if (idx === -1) idx = 0;
    if (idx >= items.length - 1) idx = items.length - 1;
    else idx = idx + 1;
    if (items[idx]) centerItem(items[idx]);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowLeft') btnPrev && !btnPrev.classList.contains('hidden') && btnPrev.click();
    if (e.key === 'ArrowRight') btnNext && !btnNext.classList.contains('hidden') && btnNext.click();
  });

  /* initial carousel position logic */
  const serverDataEl = document.getElementById('server-data');
  const serverData = serverDataEl ? JSON.parse(serverDataEl.textContent) : {};
  const preferRound = window.NEXT_ROUND || serverData.next_round || 1;
  const startIndex = items.findIndex(i => parseInt(i.getAttribute('data-round'), 10) === preferRound);
  const targetIndex = startIndex !== -1 ? startIndex : Math.min(Math.max(preferRound - 1, 0), items.length - 1);

  setTimeout(() => {
    if (items[targetIndex]) {
      centerItem(items[targetIndex], 'auto');
      setTimeout(() => {
        setActiveNearest();
        updateArrowsVisibility();
      }, 80);
    } else {
      setActiveNearest();
      updateArrowsVisibility();
    }
  }, 60);
});
