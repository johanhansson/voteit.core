from pyramid.security import authenticated_userid
from pyramid.exceptions import Forbidden
from pyramid.traversal import find_root
from pyramid.traversal import resource_path
from pyramid.renderers import render
from pyramid.view import view_config
from pyramid.response import Response
from webhelpers.html.converters import nl2br

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IDateTimeUtil
from voteit.core.security import find_authorized_userids
from voteit.core.security import VIEW
from voteit.core.models.catalog import metadata_for_query


USERINFO_TPL = 'templates/snippets/userinfo.pt'


def _truncate(text, limit=100):
    if len(text) > limit:
        return "%s<...>" % text[:limit]
    return text


@view_config(context=IMeeting, name="_userinfo", permission=VIEW)
def user_info_view(context, request, info_userid=None):
    """ Special view to allow other meeting participants to see information about a user
        who's in the same meeting as them.
    """
    root = find_root(context)

    if info_userid is None:
        info_userid = request.GET.get('userid', None)
    if info_userid is None:
        raise ValueError("No userid specified")

    def _last_entries():
        """ Return last proposals or discussion posts that this user created """
        query = {}
        #context can be user profile too
        if IMeeting.providedBy(context):
            query['path'] = resource_path(context)
        else:
            query['path'] = resource_path(root)
        query['creators'] = info_userid
        query['content_type'] = {'query':('Proposal','DiscussionPost'), 'operator':'or'}
        query['sort_index'] = 'created'
        query['reverse'] = True
        query['limit'] = 5
        return metadata_for_query(root.catalog, **query)

    if info_userid in find_authorized_userids(context, (VIEW,)):
        #User is allowed here, so do lookup
        user = root.users.get(info_userid)
    else:
        user = None

    dt_util = request.registry.getUtility(IDateTimeUtil)

    response = {}
    response['user'] = user
    response['info_userid'] = info_userid
    response['nl2br'] = nl2br
    response['last_entries'] = _last_entries()
    response['truncate'] = _truncate
    response['relative_time_format'] = dt_util.relative_time_format

    result = render(USERINFO_TPL, response, request=request)
    if request.is_xhr:
        #If this is called through a javascript, wrap in a response object
        return Response(result)
    return result
