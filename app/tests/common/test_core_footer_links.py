import re
from unittest.mock import MagicMock, patch
import pytest
from django.template.loader import render_to_string
from eventyay.base.models.page import Page
from eventyay.common.context_processors import system_information
from eventyay.control.forms.global_settings import GlobalSettingsForm
from eventyay.control.views.pages import SystemPageView


def test_global_settings_form_footer_defaults():
    with patch('eventyay.control.forms.global_settings.GlobalSettingsObject') as mock_gso:
        mock_settings = MagicMock()
        mock_settings._parent = None
        mock_settings.get.return_value = None
        mock_gso.return_value.settings = mock_settings
        form = GlobalSettingsForm()
        for key in ['events', 'terms', 'privacy', 'pricing', 'documentation', 'support']:
            assert f'footer_link_{key}_enabled' in form.fields
            assert f'footer_link_{key}_url' in form.fields
        for page_key in ['terms', 'privacy', 'pricing', 'support']:
            assert f'footer_page_{page_key}_text' in form.fields


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
