import colander

from pyramid.security import Allow, Deny, DENY_ALL
from voteit.core.models.base_content import BaseContent
from voteit.core import security


class Meeting(BaseContent):
    """ Meeting content. """
    content_type = 'Meeting'
    omit_fields_on_edit = ('name',)
    allowed_contexts = ('SiteRoot',)
    add_permission = security.ADD_MEETING

    __acl__ = [(Allow, security.ROLE_MODERATOR, (security.ALL_ADD_PERMISSIONS, security.VIEW, security.EDIT,)),
               (Allow, security.ROLE_ADMIN, (security.ALL_ADD_PERMISSIONS, security.VIEW, security.EDIT,)),
               (Allow, security.ROLE_PARTICIPANT, (security.VIEW, security.ADD_PROPOSAL,)),
               (Allow, security.ROLE_VIEWER, (security.VIEW,)),
               DENY_ALL,
               ]


class MeetingSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String())
