import json
import re
from unittest.mock import MagicMock, patch

import pytest
from django.template.loader import render_to_string

from eventyay.base.forms import I18nMarkdownTextarea
from eventyay.base.models.page import Page
from eventyay.common.context_processors import system_information
from eventyay.control.forms.global_settings import GlobalSettingsForm
from eventyay.control.views.pages import SystemPageView


def _make_mock_settings(stored=None):
    """
    Build a MagicMock that behaves like a hierarkey settings proxy.

    ``stored`` is an optional dict of key→value pairs the mock should
    return via .get().  Keys not in ``stored`` return None.
    .set() writes back into the same dict so later .get() calls see
    the value.
    """
    data = dict(stored or {})
    mock_settings = MagicMock()
    mock_settings._parent = None
    mock_settings._h = MagicMock()
    mock_settings._h.defaults = {}
    mock_settings._h.attribute_name = 'settings'
    mock_settings._h.get_declared_type.return_value = str

    def _get(key, **kwargs):
        return data.get(key, kwargs.get('default'))

    def _set(key, value):
        data[key] = value

    def _delitem(key):
        data.pop(key, None)

    def _cache():
        return dict(data)

    def _freeze():
        return dict(data)

    mock_settings.get.side_effect = _get
    mock_settings.set.side_effect = _set
    mock_settings.__delitem__ = _delitem
    mock_settings._cache.return_value = dict(data)
    mock_settings._cache.side_effect = _cache
    mock_settings.freeze.side_effect = _freeze
    return mock_settings


# ---------------------------------------------------------------------------
# GlobalSettingsForm – footer link field registration
# ---------------------------------------------------------------------------

def test_global_settings_form_footer_defaults():
    with patch('eventyay.control.forms.global_settings.GlobalSettingsObject') as mock_gso:
        mock_gso.return_value.settings = _make_mock_settings()
        form = GlobalSettingsForm()
        for key in ['events', 'terms', 'privacy', 'pricing', 'documentation', 'support']:
            assert f'footer_link_{key}_enabled' in form.fields
            assert f'footer_link_{key}_url' in form.fields
        for page_key in ['terms', 'privacy', 'pricing', 'support']:
            assert f'footer_page_{page_key}_text' in form.fields


# ---------------------------------------------------------------------------
# GlobalSettingsForm – page_locales field & field group
# ---------------------------------------------------------------------------

def test_global_settings_form_has_page_locales_field():
    """The Pages tab must include the page_locales selector."""
    with patch('eventyay.control.forms.global_settings.GlobalSettingsObject') as mock_gso:
        mock_gso.return_value.settings = _make_mock_settings()
        form = GlobalSettingsForm()
        assert 'page_locales' in form.fields
        assert form.initial.get('page_locales') == ['en']


def test_page_locales_in_pages_field_group():
    """page_locales must be first in the Pages field group."""
    with patch('eventyay.control.forms.global_settings.GlobalSettingsObject') as mock_gso:
        mock_gso.return_value.settings = _make_mock_settings()
        form = GlobalSettingsForm()
        pages_group = None
        for group_key, _, field_names in form.field_groups:
            if group_key == 'pages':
                pages_group = field_names
                break
        assert pages_group is not None, 'pages group not found'
        assert pages_group[0] == 'page_locales'


def test_page_locales_defaults_to_english():
    """When no page_locales setting is stored, default is ['en']."""
    with patch('eventyay.control.forms.global_settings.GlobalSettingsObject') as mock_gso:
        mock_gso.return_value.settings = _make_mock_settings()
        form = GlobalSettingsForm()
        assert form._page_locales == ['en']


def test_page_locales_preserves_saved_value():
    """When page_locales was previously saved, those values are used."""
    with patch('eventyay.control.forms.global_settings.GlobalSettingsObject') as mock_gso:
        mock_gso.return_value.settings = _make_mock_settings({
            'page_locales': json.dumps(['en', 'de']),
        })
        form = GlobalSettingsForm()
        assert 'en' in form._page_locales
        assert 'de' in form._page_locales


def test_page_locales_auto_includes_existing_content_locales():
    """
    If a footer page field has content in a language not in page_locales,
    that language is automatically included so translations are not hidden.
    """
    with patch('eventyay.control.forms.global_settings.GlobalSettingsObject') as mock_gso:
        mock_gso.return_value.settings = _make_mock_settings({
            'page_locales': json.dumps(['en']),
            'footer_page_terms_text': json.dumps({'en': 'Terms', 'fr': 'Conditions'}),
        })
        form = GlobalSettingsForm()
        assert 'en' in form._page_locales
        assert 'fr' in form._page_locales


# ---------------------------------------------------------------------------
# I18nMarkdownTextarea – enabled_locales filtering
# ---------------------------------------------------------------------------

def test_i18n_markdown_textarea_respects_enabled_locales():
    """Only enabled locales should be rendered; others are skipped."""
    from django import forms as dj_forms

    field = dj_forms.CharField()
    widget = I18nMarkdownTextarea(locales=['en', 'de', 'fr'], field=field)
    widget.enabled_locales = ['en', 'fr']

    html = widget.render('test_field', {'en': 'Hello', 'de': 'Hallo', 'fr': 'Bonjour'}, attrs={'id': 'id_test'})

    # English and French should appear; German should NOT
    assert 'data-lang="en"' in html
    assert 'data-lang="fr"' in html
    assert 'data-lang="de"' not in html


def test_i18n_markdown_textarea_renders_all_when_no_filter():
    """When enabled_locales equals locales, all languages should render."""
    from django import forms as dj_forms

    field = dj_forms.CharField()
    widget = I18nMarkdownTextarea(locales=['en', 'de'], field=field)

    html = widget.render('test_field', {'en': 'Hello', 'de': 'Hallo'}, attrs={'id': 'id_test'})

    assert 'data-lang="en"' in html
    assert 'data-lang="de"' in html


# ---------------------------------------------------------------------------
# Context processor – core footer links
# ---------------------------------------------------------------------------

def test_context_processor_core_footer_links(rf):
    request = rf.get('/')
    with patch('eventyay.common.context_processors.GlobalSettingsObject') as mock_gso:
        mock_settings = MagicMock()
        mock_settings.get.side_effect = lambda k, **kwargs: (
            True if 'enabled' in k else kwargs.get('default', '')
        )
        mock_gso.return_value.settings = mock_settings
        ctx = system_information(request)
        assert 'core_footer_links' in ctx
        keys = [link['key'] for link in ctx['core_footer_links']]
        assert 'events' in keys
        assert 'terms' in keys
        assert 'privacy' in keys
        assert 'pricing' in keys
        assert 'documentation' in keys
        assert 'support' in keys


# ---------------------------------------------------------------------------
# SystemPageView – slug handling and custom content
# ---------------------------------------------------------------------------

def test_system_page_view_slug_handling():
    # Test setting slug attribute directly
    view = SystemPageView()
    view.slug = 'terms'
    assert view.get_slug() == 'terms'

    # Test via view.kwargs URL dispatch
    view_kwargs = SystemPageView()
    view_kwargs.kwargs = {'slug': 'privacy'}
    assert view_kwargs.get_slug() == 'privacy'

    with patch('eventyay.control.views.pages.Page.objects.get') as mock_get:
        mock_page_terms = MagicMock(title='Terms of Service', slug='terms')
        mock_page_privacy = MagicMock(title='Privacy Policy', slug='privacy')
        mock_get.side_effect = lambda slug: mock_page_privacy if slug == 'privacy' else mock_page_terms

        assert view.get_page() == mock_page_terms
        assert view_kwargs.get_page() == mock_page_privacy


def test_system_page_view_custom_content():
    view = SystemPageView()
    view.slug = 'privacy'

    with patch('eventyay.control.views.pages.Page.objects.get', side_effect=Page.DoesNotExist):
        with patch('eventyay.control.views.pages.GlobalSettingsObject') as mock_gso:
            mock_settings = MagicMock()
            mock_settings.get.side_effect = lambda k, **kwargs: (
                '# Custom Privacy Content' if k == 'footer_page_privacy_text' else True
            )
            mock_gso.return_value.settings = mock_settings
            page = view.get_page()
            assert page.title == 'Privacy Policy'
            assert str(page.text) == '# Custom Privacy Content'


# ---------------------------------------------------------------------------
# Core footer template structure
# ---------------------------------------------------------------------------

def test_core_footer_template_structure():
    sample_links = [
        {'key': 'events', 'label': 'Events', 'url': '/upcoming', 'target_blank': False},
        {'key': 'terms', 'label': 'Terms', 'url': '/terms', 'target_blank': False},
        {'key': 'documentation', 'label': 'Documentation', 'url': 'https://docs.eventyay.com', 'target_blank': True},
    ]
    html = render_to_string('common/includes/core_footer.html', {'core_footer_links': sample_links})

    assert 'core-footer-nav' in html
    assert 'core-footer-links-container' in html

    def anchor_for(fragment):
        match = re.search(rf'<a[^>]*href="[^"]*{re.escape(fragment)}[^"]*"[^>]*>', html)
        assert match, f'no anchor found containing {fragment!r}'
        return match.group()

    # Internal links must NOT open in a new tab
    events_a = anchor_for('upcoming')
    assert 'target="_blank"' not in events_a

    terms_a = anchor_for('terms')
    assert 'target="_blank"' not in terms_a

    # External link must open in a new tab with rel="noopener"
    docs_a = anchor_for('docs.eventyay.com')
    assert 'target="_blank"' in docs_a
    assert 'rel="noopener"' in docs_a

    assert 'Events' in html
    assert 'Terms' in html
    assert 'Documentation' in html
