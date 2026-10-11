(() => {
  'use strict';
  document.querySelectorAll('[data-order-action]').forEach(form => {
    form.addEventListener('submit', event => {
      if (form.dataset.confirm && !window.confirm(form.dataset.confirm)) {
        event.preventDefault();
        return;
      }
      // Preserve the submitted action input while preventing accidental double clicks.
      form.querySelector('button[type="submit"]').disabled = true;
    });
  });
  window.addEventListener('pageshow', () => {
    document.querySelectorAll('[data-order-action] button').forEach(button => { button.disabled = false; });
  });
})();
