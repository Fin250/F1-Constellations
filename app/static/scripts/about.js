(function(){
  const trigger = document.getElementById('trackTrigger');
  const menu = document.getElementById('trackDropdown');
  const label = trigger.querySelector('.track-select-label');

  function openMenu() {
    const rect = trigger.getBoundingClientRect();
    menu.style.left = `${rect.left}px`;
    menu.style.top  = `${rect.bottom + 6}px`;
    menu.style.minWidth = `${rect.width}px`;
    menu.hidden = false;
    trigger.setAttribute('aria-expanded', 'true');
  }
  function closeMenu() {
    menu.hidden = true;
    trigger.setAttribute('aria-expanded', 'false');
  }
  function toggleMenu() {
    if (menu.hidden) openMenu(); else closeMenu();
  }

  trigger.addEventListener('click', (e) => {
    e.stopPropagation();
    toggleMenu();
  });

  menu.addEventListener('click', (e) => {
    const li = e.target.closest('.track-select-item');
    if (!li) return;
    const name = li.querySelector('.track-select-name')?.textContent?.trim() || 'Track';
    const href = li.dataset.href;
    label.textContent = name;
    closeMenu();
    if (href) window.location.href = href;
  });

  menu.addEventListener('keydown', (e) => {
    const items = [...menu.querySelectorAll('.track-select-item')];
    const idx = items.indexOf(document.activeElement);
    if (e.key === 'ArrowDown') { e.preventDefault(); (items[idx+1] || items[0]).focus(); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); (items[idx-1] || items[items.length-1]).focus(); }
    else if (e.key === 'Enter') { document.activeElement.click(); }
    else if (e.key === 'Escape') { closeMenu(); trigger.focus(); }
  });

  document.addEventListener('click', (e) => {
    if (!menu.hidden && !trigger.contains(e.target) && !menu.contains(e.target)) closeMenu();
  });
  window.addEventListener('resize', () => { if (!menu.hidden) openMenu(); });
  window.addEventListener('scroll', () => { if (!menu.hidden) openMenu(); }, true);
})();