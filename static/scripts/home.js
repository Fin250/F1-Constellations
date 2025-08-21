const serverDataEl = document.getElementById('server-data');
const serverData = serverDataEl ? JSON.parse(serverDataEl.textContent) : {};
window.NEXT_ROUND = serverData.next_round;

document.addEventListener('DOMContentLoaded', function () {
  const carousel = document.getElementById('trackCarousel');
  if (!carousel) return;

  const items = Array.from(carousel.querySelectorAll('.box'));
  if (items.length === 0) return;

  function centerItem(el, behaviour = 'smooth') {
    const left = el.offsetLeft - (carousel.clientWidth - el.clientWidth) / 2;
    carousel.scrollTo({ left, behavior: behaviour });
  }

  function applyDetailedBackgroundsFromServerData() {
    const serverEl = document.getElementById('server-data');
    if (!serverEl) return;
    let server;
    try {
      server = JSON.parse(serverEl.textContent || '{}');
    } catch (err) {
      return;
    }
    const tracks = server.tracks || [];
    const carousel = document.getElementById('trackCarousel');
    if (!carousel) return;
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
        box.style.backgroundImage = '';
        box.classList.remove('has-detailed-bg');
      }
    });
  }

  // apply backgrounds immediately on load
  applyDetailedBackgroundsFromServerData();

  function setActiveNearest() {
    const center = carousel.scrollLeft + carousel.clientWidth / 2;
    let nearest = null;
    let minDist = Infinity;

    items.forEach(item => {
      const itemCenter = item.offsetLeft + item.offsetWidth / 2;
      const dist = Math.abs(center - itemCenter);
      if (dist < minDist) {
        minDist = dist;
        nearest = item;
      }
    });

    items.forEach(i => i.classList.toggle('active', i === nearest));

    const quickpickArrow = document.getElementById('quickpick-arrow');
    const quickpickItems = Array.from(document.querySelectorAll('.quickpick-item'));

    function updateArrow() {
      const active = carousel.querySelector('.box.active');
      if (!active) return;

      const idx = items.indexOf(active);
      if (idx === -1 || !quickpickItems[idx]) return;

      const target = quickpickItems[idx];
      const rect = target.getBoundingClientRect();
      const barRect = document.querySelector('.quickpick-bar').getBoundingClientRect();

      const center = rect.left + rect.width / 2 - barRect.left;
      quickpickArrow.style.left = `${center - 8}px`;
    }

    updateArrow();
    window.addEventListener('resize', updateArrow);
  }

  let scrollTimer = null;
  carousel.addEventListener('scroll', function () {
    setActiveNearest();
    if (scrollTimer) clearTimeout(scrollTimer);
    scrollTimer = setTimeout(() => setActiveNearest(), 100);
  });

  window.addEventListener('resize', () => setActiveNearest());

  const btnPrev = document.querySelector('.carousel-btn.prev');
  const btnNext = document.querySelector('.carousel-btn.next');

  function indexOfActive() {
    return items.findIndex(i => i.classList.contains('active'));
  }

  if (btnPrev) btnPrev.addEventListener('click', function () {
    let idx = indexOfActive();
    if (idx <= 0) idx = 0;
    else idx = idx - 1;
    centerItem(items[idx]);
  });

  if (btnNext) btnNext.addEventListener('click', function () {
    let idx = indexOfActive();
    if (idx === -1) idx = 0;
    if (idx >= items.length - 1) idx = items.length - 1;
    else idx = idx + 1;
    centerItem(items[idx]);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowLeft') btnPrev && btnPrev.click();
    if (e.key === 'ArrowRight') btnNext && btnNext.click();
  });

  const preferRound = window.NEXT_ROUND || 1;
  const startIndex = items.findIndex(i => parseInt(i.getAttribute('data-round'), 10) === preferRound);
  const targetIndex = startIndex !== -1 ? startIndex : Math.min(Math.max(preferRound - 1, 0), items.length - 1);

  setTimeout(() => {
    if (items[targetIndex]) {
      centerItem(items[targetIndex], 'auto');
      setTimeout(setActiveNearest, 80);
    } else {
      setActiveNearest();
    }
  }, 60);
});
