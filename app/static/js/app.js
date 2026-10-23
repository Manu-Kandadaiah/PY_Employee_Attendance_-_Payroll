(() => {
  const clock = document.getElementById('liveClock');
  if (clock) {
    const update = () => { clock.textContent = new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit', second:'2-digit'}); };
    update(); setInterval(update, 1000);
  }
  document.querySelectorAll('[data-auto-dismiss]').forEach(el => setTimeout(() => bootstrap.Alert.getOrCreateInstance(el).close(), 5000));
  document.querySelectorAll('form[data-confirm]').forEach(form => form.addEventListener('submit', e => { if (!confirm(form.dataset.confirm)) e.preventDefault(); }));
})();
