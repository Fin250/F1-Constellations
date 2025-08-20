document.addEventListener('DOMContentLoaded', function () {
  const carousel = document.getElementById('trackCarousel');
  if (!carousel) return;

  const items = Array.from(carousel.querySelectorAll('.box'));
  if (items.length === 0) return;

  function centerItem(el, behaviour = 'smooth') {
    const left = el.offsetLeft - (carousel.clientWidth - el.clientWidth) / 2;
    carousel.scrollTo({ left, behavior: behaviour });
  }

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

    const originalSetActive = setActiveNearest;
    setActiveNearest = function() {
      originalSetActive();
      updateArrow();
    };

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

  // temporary start hardcode
  const preferIndex = 13;
  const startIndex = Math.min(preferIndex, items.length - 1);
  setTimeout(() => {
    if (items[startIndex]) {
      centerItem(items[startIndex], 'auto');
      setTimeout(setActiveNearest, 80);
    } else {
      setActiveNearest();
    }
  }, 60);
});