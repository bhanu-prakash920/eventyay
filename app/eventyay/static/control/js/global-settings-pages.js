// Sync i18n textarea visibility with selected page languages.

function getPageLocalesCheckboxes() {
  return document.querySelectorAll('input[type="checkbox"][name="page_locales"]');
}

function getSelectedLocales(checkboxes) {
  const selected = [];
  checkboxes.forEach((cb) => {
    if (cb.checked) {
      selected.push(cb.value);
    }
  });
  return selected;
}

function syncTextareaVisibility(selectedLocales) {
  const wrappers = document.querySelectorAll('.i18n-textarea-wrapper[data-lang]');
  wrappers.forEach((wrapper) => {
    const lang = wrapper.getAttribute('data-lang');
    const isVisible = selectedLocales.includes(lang);
    wrapper.style.display = isVisible ? '' : 'none';
    if (isVisible) {
      wrapper.removeAttribute('hidden');
    } else {
      wrapper.setAttribute('hidden', '');
    }
  });
}

function init() {
  const checkboxes = getPageLocalesCheckboxes();
  if (checkboxes.length === 0) return;

  // React to checkbox changes
  checkboxes.forEach((cb) => {
    cb.addEventListener('change', () => {
      syncTextareaVisibility(getSelectedLocales(checkboxes));
    });
  });

  // Initial visibility sync
  syncTextareaVisibility(getSelectedLocales(checkboxes));
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// Ensure sync after full window load
window.addEventListener('load', init);
