import colander
import deform
from pyramid.traversal import resource_path, find_interface
from repoze.catalog.query import Eq

from voteit.core import _
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.models.interfaces import IProposal
from voteit.core.validators import html_string_validator


@colander.deferred
def poll_plugin_choices_widget(node, kw):
    request = kw['request']
    values = []
    values.extend([(x.name, x.factory) for x in request.registry.registeredAdapters() if
                   x.provided == IPollPlugin])
    return deform.widget.RadioChoiceWidget(values=values, template="object_radio_choice")


@colander.deferred
def proposal_choices_widget(node, kw):
    context = kw['context']
    # Proposals to vote on
    proposal_choices = []
    agenda_item = find_interface(context, IAgendaItem)
    if agenda_item is None:
        Exception("Couldn't find the agenda item from this polls context")
    # Get valid proposals - should be in states 'published' to be selectable
    for prop in agenda_item.get_content(iface=IProposal, states='published', sort_on='created'):
        proposal_choices.append((prop.uid, "#%s | %s" % (prop.aid, prop.title)))
    return deform.widget.CheckboxChoiceWidget(values=proposal_choices)


@colander.deferred
def deferred_default_poll_method(node, kw):
    request = kw['request']
    return request.registry.settings.get('default_poll_method', '')


@colander.deferred
def poll_default_title(node, kw):
    request = kw['request']
    query = Eq('path', resource_path(request.agenda_item)) & Eq('type_name', 'Poll')
    res = request.root.catalog.query(query)[0]
    title = _("Descision ${num}", mapping={'num': res.total + 1})
    return request.localizer.translate(title)


class PollSchema(colander.MappingSchema):
    title = colander.SchemaNode(
        colander.String(),
        title=_(u"Title"),
        default=poll_default_title,
        validator=html_string_validator,
    )
    description = colander.SchemaNode(
        colander.String(),
        title=_("Description"),
        missing="",
        description=_(u"poll_description_description",
                      default=u"Explain your choice of poll method and your plan for the different "
                              u"polls in the agenda item."),
        widget=deform.widget.TextAreaWidget(rows=5, cols=40),
        validator=html_string_validator,
    )
    poll_plugin = colander.SchemaNode(
        colander.String(),
        title=_(u"Poll method to use"),
        description=_(u"poll_poll_plugin_description",
                      default=u"Each poll method should have its own documentation. "
                              u"The standard ones from VoteIT will be in the manual - check the help menu!"),
        widget=poll_plugin_choices_widget,
        default=deferred_default_poll_method,
    )


class PollEditProposalsSchema(colander.Schema):
    proposals = colander.SchemaNode(
        colander.Set(),
        title=_(u"Proposals"),
        description=_(u"poll_proposals_description",
                      default=u"Only proposals in the state 'published' can be selected"),
        missing=set(),
        widget=proposal_choices_widget,
    )


def includeme(config):
    # config.add_content_schema('Poll', AddPollSchema, 'add')
    config.add_content_schema('Poll', PollSchema, ['add', 'edit'])
    config.add_content_schema('Poll', PollEditProposalsSchema, 'edit_proposals')
