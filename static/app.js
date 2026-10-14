document.querySelectorAll('form[data-confirm]').forEach(form => {
  form.addEventListener('submit', event => {
    if (!window.confirm(form.dataset.confirm)) event.preventDefault();
  });
});
document.querySelectorAll('input, textarea, select').forEach(field => {
  if (field.id && document.querySelector(`label[for="${field.id}"]`) && field.required) {
    document.querySelector(`label[for="${field.id}"]`).classList.add('required-label');
  }
});
