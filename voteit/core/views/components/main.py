from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from betahaus.viewcomponent.interfaces import IViewGroup

from voteit.core import VoteITMF as _


@view_action('main', 'columns')
def columns(context, request, *args, **kwargs):
    api = kwargs['api']
    group_name = kwargs['group_name']
    util = request.registry.getUtility(IViewGroup, name = group_name)
    response = {}

    #Col 1
    col_one_name = kwargs['col_one'] #Required
    col_one_va = util.get(col_one_name, None)
    if col_one_va:
        response['column_one'] = col_one_va(context, request, api = api)
    else:
        response['column_one'] = "Error: Can't find view action '%s' in group '%s'." % (col_one_name, group_name)

    #Col 2
    col_two_name = kwargs.get('col_two', None)
    if not col_two_name:
        return render('../templates/snippets/one_column.pt', response, request = request)

    col_two_va = util.get(col_two_name, None)
    if col_two_va:
        response['column_two'] = col_two_va(context, request, api = api)
    else:
        response['column_two'] = "Error: Can't find view action '%s' in group '%s'." % (col_two_name, group_name)
    return render('../templates/snippets/two_columns.pt', response, request = request)


@view_action('main', 'flash_messages')
def render_flash_messages(context, request, *args, **kwargs):
    """ Render flash messages. """
    api = kwargs['api']
    try:
        if api.meeting_state == u'upcoming':
            msg = _(u"This meeting hasn't started yet.")
            api.flash_messages.add(msg, type = 'lock')
        if api.meeting_state == u'closed':
            msg = _(u"This meeting has closed.")
            api.flash_messages.add(msg, type = 'lock')
    except Exception:
        pass
    response = dict(messages = api.flash_messages.get_messages(),)
    return render('../templates/snippets/flash_messages.pt', response, request = request)


@view_action('main', 'poll_state_info')
def render_poll_state_info(context, request, *args, **kwargs):
    response = dict(
        api = kwargs['api'],
        wf_state = context.get_workflow_state(),
        poll = context,
    )
    return render('../templates/snippets/poll_state_info.pt', response, request = request)


