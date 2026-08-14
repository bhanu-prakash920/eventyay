/**
 * Global Settings Pages tab – reactive language visibility.
 *
 * When the admin selects or deselects languages in the MultipleLanguagesWidget
 * (page_locales), this module dynamically shows or hides the corresponding
 * `.i18n-textarea-wrapper[data-lang]` elements across all markdown fields.
 *
 * ES module, no jQuery, no inline scripts — CSP compliant.
 */

function getPageLocalesWidget() {
  // The MultipleLanguagesWidget renders checkboxes with name="page_locales"
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
    if (selectedLocales.includes(lang)) {
      wrapper.style.display = '';
      wrapper.removeAttribute('hidden');
    } else {
      wrapper.style.display = 'none';
      wrapper.setAttribute('hidden', '');
    }
  });
}

function init() {
  const checkboxes = getPageLocalesWidget();
  if (checkboxes.length === 0) return;

  // Listen for change events on the language grid checkboxes
  checkboxes.forEach((cb) => {
    cb.addEventListener('change', () => {
      syncTextareaVisibility(getSelectedLocales(checkboxes));
    });
  });

  // Initial sync on page load
  syncTextareaVisibility(getSelectedLocales(checkboxes));
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// Re-run after full load to catch any late-rendered widgets
window.addEventListener('load', init);
