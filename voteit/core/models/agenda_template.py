from __future__ import unicode_literals

from zope.interface import implementer
from pyramid.security import Allow
from pyramid.security import DENY_ALL

from voteit.core import _
from voteit.core import security
from voteit.core.helpers import generate_slug
from voteit.core.models.arche_compat import createContent
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IAgendaTemplate


@implementer(IAgendaTemplate)
class AgendaTemplate(BaseContent):
    """ Agenda template content type.
        See :mod:`voteit.core.models.interfaces.IAgendaTemplate`.
        All methods are documented in the interface of this class.
    """
    type_name = 'AgendaTemplate'
    type_title = _("Agenda template")
    add_permission = security.ADD_AGENDA_TEMPLATE
    schemas = {'add': 'AgendaTemplateSchema', 'edit': 'AgendaTemplateSchema'}

    __acl__ = [(Allow, security.ROLE_ADMIN, (security.EDIT, security.VIEW, security.DELETE, security.MANAGE_SERVER, )),
               (Allow, security.ROLE_OWNER, (security.EDIT, security.VIEW, security.DELETE,)),
               DENY_ALL,
              ]
    
    def populate_meeting(self, meeting):
        for item in self.get_field_value('agenda_items', ()):
            obj = createContent('AgendaItem', **item)
            slug = generate_slug(meeting, obj.title)
            meeting[slug] = obj


def includeme(config):
    config.add_content_factory(AgendaTemplate, addable_to = 'AgendaTemplates')
