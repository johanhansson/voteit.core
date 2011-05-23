import unittest

from pyramid import testing
from zope.interface.verify import verifyObject
from zope.component import queryUtility
from pyramid.threadlocal import get_current_registry



    
class PollTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    def _make_obj(self):
        from voteit.core.models.poll import Poll
        return Poll()
    
    def _register_majority_poll(self, poll):
        from voteit.core import register_poll_plugin
        from voteit.core.plugins.majority_poll import MajorityPollPlugin
        registry = get_current_registry()
        register_poll_plugin(MajorityPollPlugin, registry=registry)

    def _agenda_item_with_proposals_fixture(self):
        """ Create an agenda item with a poll and two proposals. """
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.proposal import Proposal
        agenda_item = AgendaItem()
        agenda_item['prop1'] = Proposal()
        agenda_item['prop2'] = Proposal()
        return agenda_item

    def _make_vote(self, vote_data='hello_world'):
        from voteit.core.models.vote import Vote
        vote = Vote()
        vote.set_vote_data(vote_data)
        return vote

    def test_implements_base_content(self):
        from voteit.core.models.interfaces import IBaseContent
        obj = self._make_obj()
        self.assertTrue(verifyObject(IBaseContent, obj))

    def test_implements_poll(self):
        from voteit.core.models.interfaces import IPoll
        obj = self._make_obj()
        self.assertTrue(verifyObject(IPoll, obj))

    def test_proposal_uids(self):
        """ Proposal uids should be a setable property that connects to
            the dynamic field "proposals".
        """
        obj = self._make_obj()
        obj.proposal_uids = ['hello']
        self.assertEqual(obj.get_field_value('proposals'), ['hello'])
        obj.set_field_value('proposals', ('new', 'uids',))
        self.assertEqual(obj.proposal_uids, ('new', 'uids',))

    def test_poll_plugin_name(self):
        """ poll_plugin_name should get the registered plugins name. """
        obj = self._make_obj()
        obj.set_field_value('poll_plugin', 'my_plugin')
        self.assertEqual(obj.poll_plugin_name, 'my_plugin')
    
    def test_get_proposal_objects(self):
        """ Test that all proposals that belong to this poll gets returned. """
        agenda_item = self._agenda_item_with_proposals_fixture()
        prop1 = agenda_item['prop1']
        prop2 = agenda_item['prop2']
        agenda_item['poll'] = poll = self._make_obj()
        poll.proposal_uids = (prop1.uid, prop2.uid,)
        
        self.assertEqual(set(poll.get_proposal_objects()), set([prop1, prop2,]))
    
    def test_get_all_votes(self):
        """ Get all votes for the current poll. """
        obj = self._make_obj()
        obj['me'] = self._make_vote()
        self.assertEqual(tuple(obj.get_all_votes()), (obj['me'],))

    def test_get_voted_userids(self):
        obj = self._make_obj()
        vote1 = self._make_vote()
        vote1.creators = ['admin']
        vote2 = self._make_vote()
        vote2.creators = ['some_guy']
        obj['vote1'] = vote1
        obj['vote2'] = vote2

        self.assertEqual(obj.get_voted_userids(), frozenset(['admin', 'some_guy']))

    def test_get_ballots_string(self):
        obj = self._make_obj()
        #Make some default votes
        vote1 = self._make_vote()
        vote2 = self._make_vote()
        obj['vote1'] = vote1
        obj['vote2'] = vote2
        
        #And one other vote
        vote3 = self._make_vote()
        vote3.set_vote_data('other')
        obj['vote3'] = vote3

        self.assertEqual(obj.get_ballots(), [{'count': 2, 'ballot': 'hello_world'}, {'count': 1, 'ballot': 'other'}])

    def test_ballots_object(self):
        obj = self._make_obj()
        
        #Unique choices
        choice1 = object()
        choice2 = object()

        obj['vote1'] = self._make_vote(choice1)
        obj['vote2'] = self._make_vote(choice1)
        obj['vote3'] = self._make_vote(choice1)
        obj['vote4'] = self._make_vote(choice2)
        obj['vote5'] = self._make_vote(choice2)

        expected = [{'count': 2, 'ballot': choice2}, {'count': 3, 'ballot': choice1}]
        result = obj.get_ballots()
        result.sort(key=lambda x: x['count'])
        
        self.assertEqual(result, expected)

    def test_ballots_dict(self):
        obj = self._make_obj()
        
        #Unique choices
        choice1 = {'apple':1, 'potato':2}
        choice2 = {'apple':1}

        obj['vote1'] = self._make_vote(choice1)
        obj['vote2'] = self._make_vote(choice1)
        obj['vote3'] = self._make_vote(choice1)
        obj['vote4'] = self._make_vote(choice2)
        obj['vote5'] = self._make_vote(choice2)

        #Keep an eye on this. Dicts aren't hashable so this may fail due to ordering in the list.
        expected = [{'count': 2, 'ballot': choice2}, {'count': 3, 'ballot': choice1}]
        result = obj.get_ballots()
        result.sort(key=lambda x: x['count'])
        
        self.assertEqual(result, expected)
    
    def _load_workflows(self):
        from voteit.core import register_workflows
        register_workflows()
    
    def _make_obj(self):
        from voteit.core.models.poll import Poll
        return Poll()

    def _extract_transition_names(self, info):
        return set([x['name'] for x in info])

    def test_poll_transitions(self):
        self._load_workflows()
        
        #Setup for proper test
        obj = self._make_obj()
        self._register_majority_poll(obj)
        obj.set_field_value('poll_plugin', u'majority_poll')
        
        #Initial state
        self.assertEqual(obj.get_workflow_state, u'private')
        
        #private -> planned
        obj.make_workflow_transition('private_to_planned')
        self.assertEqual(obj.get_workflow_state, u'planned')

        #planned -> private
        obj.make_workflow_transition('planned_to_private')
        self.assertEqual(obj.get_workflow_state, u'private')

        #planned -> ongoing
        obj.reset_workflow()
        obj.set_workflow_state('planned')
        obj.make_workflow_transition('planned_to_ongoing')
        self.assertEqual(obj.get_workflow_state, u'ongoing')

        #planned -> canceled
        obj.reset_workflow()
        obj.set_workflow_state('planned')
        obj.make_workflow_transition('planned_to_canceled')
        self.assertEqual(obj.get_workflow_state, u'canceled')

        #ongoing -> closed
        obj.reset_workflow()
        obj.set_workflow_state('planned')
        obj.set_workflow_state('ongoing')
        obj.make_workflow_transition('ongoing_to_closed')
        self.assertEqual(obj.get_workflow_state, u'closed')

    def test_available_transitions(self):
        self._load_workflows()
        
        #Setup for proper test
        obj = self._make_obj()
        self._register_majority_poll(obj)
        obj.set_field_value('poll_plugin', u'majority_poll')
        
        #Private - Initial state
        result = self._extract_transition_names(obj.get_available_workflow_states())
        self.assertEqual(result, set([u'planned']))
        
        #Planned
        obj.set_workflow_state('planned')
        result = self._extract_transition_names(obj.get_available_workflow_states())
        self.assertEqual(result, set([u'private', u'ongoing', u'canceled']))

        #Ongoing
        obj.set_workflow_state('ongoing')
        result = self._extract_transition_names(obj.get_available_workflow_states())
        self.assertEqual(result, set([u'closed']))

        #Canceled
        obj.reset_workflow()
        obj.set_workflow_state('planned')
        obj.set_workflow_state('canceled')
        result = self._extract_transition_names(obj.get_available_workflow_states())
        self.assertEqual(result, set())

        #Closed
        obj.reset_workflow()
        obj.set_workflow_state('planned')
        obj.set_workflow_state('ongoing')
        obj.set_workflow_state('closed')
        result = self._extract_transition_names(obj.get_available_workflow_states())
        self.assertEqual(result, set())