from unittest.mock import MagicMock, patch
import pytest
from django.template import Context, Template
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


def test_context_processor_core_footer_links(rf):
    request = rf.get('/')
    with patch('eventyay.base.settings.GlobalSettingsObject') as mock_gso:
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
    view = SystemPageView()
    view.slug = 'terms'
    assert view.get_slug() == 'terms'

    with patch('eventyay.control.views.pages.Page.objects.get') as mock_get:
        mock_page = MagicMock(title='Terms of Service', slug='terms')
        mock_get.return_value = mock_page
        assert view.get_page() == mock_page


def test_core_footer_template_structure():
    template_str = """
    {% if core_footer_links %}
    <nav class="core-footer-nav">
        <ul>
            {% for link in core_footer_links %}
            <li><a href="{{ link.url }}">{{ link.label }}</a></li>
            {% endfor %}
        </ul>
    </nav>
    {% endif %}
    """
    t = Template(template_str)
    sample_links = [
        {'key': 'events', 'label': 'Events', 'url': '/upcoming', 'target_blank': False},
        {'key': 'terms', 'label': 'Terms', 'url': '/terms', 'target_blank': False},
        {'key': 'documentation', 'label': 'Documentation', 'url': 'https://docs.eventyay.com', 'target_blank': True},
    ]
    html = t.render(Context({'core_footer_links': sample_links}))
    assert '<nav class="core-footer-nav">' in html
    assert 'href="/upcoming"' in html
    assert 'href="/terms"' in html
    assert 'href="https://docs.eventyay.com"' in html
    assert 'Events' in html
    assert 'Terms' in html
    assert 'Documentation' in html
