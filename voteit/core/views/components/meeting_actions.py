from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from pyramid.traversal import resource_path
from voteit.core.security import MANAGE_SERVER, MODERATE_MEETING
from voteit.core import VoteITMF as _


MODERATOR_SECTIONS = ('closed', 'ongoing', 'upcoming', 'private',)
REGULAR_SECTIONS = ('closed', 'ongoing', 'upcoming',)


@view_action('main', 'meeting_actions')
def meeting_actions(context, request, va, **kw):
    """ This is the main renderer for meeting actions.
        The structure of the menu. it will call all view components
        in the group meeting_actions.
        In turn, some of those will call other groups.
    """
    api = kw['api']
    return """<ul id="meeting-actions-menu">%s</ul>""" % api.render_view_group(context, request, 'meeting_actions')


@view_action('meeting_actions', 'meetings', title = _(u"Meetings"))
def meetings_menu(context, request, va, **kw):
    api = kw['api']
    if not api.userid:
        return ''
    principals = api.context_effective_principals(api.root)
    query = dict(
        content_type = 'Meeting',
        view_meeting_userids = api.userid,
    )
    response = {}
    response['api'] = api
    response['menu_title'] = api.translate(va.title)
    response['meetings'] = api.get_metadata_for_query(**query)
    return render('../templates/snippets/meetings_menu.pt', response, request = request)


@view_action('meeting_actions', 'polls', title = _(u"Polls"))
def polls_menu(context, request, va, **kw):
    api = kw['api']
    if api.meeting is None:
        return ''

    if api.show_moderator_actions:
        sections = MODERATOR_SECTIONS
    else:
        sections = REGULAR_SECTIONS

    metadata = {}
    meeting_path = resource_path(api.meeting)
    show_polls = False
    for section in sections:
        #Note, as long as we don't query for private wf state, we don't have to check perms
        metadata[section] = api.get_metadata_for_query(content_type = 'Poll',
                                                        path = meeting_path,
                                                        workflow_state = section)
        if metadata[section]:
            show_polls = True

    response = {}
    response['api'] = api
    response['sections'] = sections
    response['show_polls'] = show_polls
    response['polls_metadata'] = metadata
    response['menu_title'] = va.title
    #Unread
    query = dict(
        content_type = 'Poll',
        path = meeting_path,
        unread = api.userid,
        #Not checking allowed to view is okay here, since polls don't get added to unread when they're private
        #If that would change, the line below will fix it, so it's kept around so we don't forget :)
        #allowed_to_view = {'operator': 'or', 'query': api.context_effective_principals(api.meeting)},
    )
    response['unread_polls_count'] = api.search_catalog(**query)[0]
    return render('../templates/snippets/polls_menu.pt', response, request = request)


@view_action('meeting_actions', 'participants', title = _(u"Participants"))
def participants_tab(context, request, va, **kw):
    api = kw['api']
    if not api.userid or not api.meeting:
        return ''
    link = '%s@@participants' % api.resource_url(api.meeting, request)
    return """ <li class="tab"><a href="%s">%s</a></li>"""  % (link, api.translate(va.title))


@view_action('meeting_actions', 'admin_menu', title = _(u"Admin menu"), permission = MANAGE_SERVER)
@view_action('meeting_actions', 'moderator_menu', title = _(u"Moderator"), permission = MODERATE_MEETING, meeting_only = True)
def generic_menu(context, request, va, **kw):
    if va.kwargs.get('meeting_only', False) == True:
        return ''
    api = kw['api']
    response = {}
    response['menu_title'] = va.title
    response['menu_css_cls'] = 'cog-dark'
    response['rendered_menu'] = api.render_view_group(api.root, request, va.name)
    return render('../templates/snippets/generic_meeting_menu.pt', response, request = request)


@view_action('admin_menu', 'edit_root_permissions', title = _(u"Root permissions"), link = "@@permissions")
@view_action('admin_menu', 'server_log', title = _(u"Server logs"), link = "@@server_logs")
def generic_root_menu_link(context, request, va, **kw):
    """ This is for simple menu items for the root """
    api = kw['api']
    url = api.resource_url(api.root, request) + va.kwargs['link']
    return """<li><a href="%s">%s</a></li>""" % (url, api.translate(va.title))


@view_action('moderator_menu', 'permissions', title = _(u"Edit permissions"), link = "@@permissions")
@view_action('moderator_menu', 'logs', title = _(u"Meeting actions log"), link = "@@logs")
@view_action('moderator_menu', 'manage_layout', title = _(u"Layout and widgets"), link = "@@manage_layout")
@view_action('moderator_menu', 'add_tickets', title = _(u"Invite participants"), link = "@@add_tickets")
@view_action('moderator_menu', 'manage_tickets', title = _(u"Manage invites"), link = "@@manage_tickets")
def generic_moderator_menu_link(context, request, va, **kw):
    """ This is for simple menu items for the meeting root """
    api = kw['api']
    url = api.resource_url(api.meeting, request) + va.kwargs['link']
    return """<li><a href="%s">%s</a></li>""" % (url, api.translate(va.title))