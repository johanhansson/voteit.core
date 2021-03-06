from __future__ import unicode_literals

import colander
import deform

from voteit.core import VoteITMF as _
from voteit.core.schemas.common import deferred_default_hashtag_text
from voteit.core.schemas.common import random_oid
from voteit.core.validators import NotOnlyDefaultTextValidator


@colander.deferred
def deferred_default_proposal_text(node, kw):
    """ Proposals usualy start with "I propose" or something similar.
        This will be the default text, unless there's a hashtag present.
        In that case the hashtag will be default.
        
        This might be used in the context of an agenda item or a proposal.
    """
    request = kw['request']
    hashtag_text = deferred_default_hashtag_text(node, kw)
    proposal_default_text = request.localizer.translate(_(u"proposal_default_text", default = u"proposes"))
    return "%s %s" % (proposal_default_text, hashtag_text)


@colander.deferred    
def deferred_proposal_text_validator(node, kw):
    context = kw['context']
    request = kw['request']
    return NotOnlyDefaultTextValidator(context, request, deferred_default_proposal_text)


class ProposalSchema(colander.MappingSchema):
    text = colander.SchemaNode(colander.String(),
                                title = _(u"Proposal"),
                                description = _("proposal_text_description",
                                                default = "A proposal is a statement the meeting can approve or deny. "
                                    "You may use an at sign to reference a user (ex: 'hello @jane') or a hashtag (ex: '#budget') "
                                    "to reference or create a tag. All proposals automatically get their own tag."),
                                validator = deferred_proposal_text_validator,
                                default = deferred_default_proposal_text,
                                oid = random_oid,
                                widget = deform.widget.TextAreaWidget(rows=3),)


def includeme(config):
    config.add_content_schema('Proposal', ProposalSchema, ('add', 'edit'))
