import unittest
from datetime import datetime

from pyramid import testing
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import Authenticated
from zope.interface.verify import verifyObject

from voteit.core import security


admin = set([security.ROLE_ADMIN])
moderator = set([security.ROLE_MODERATOR])
authenticated = set([Authenticated])
participant = set([security.ROLE_PARTICIPANT])
viewer = set([security.ROLE_VIEWER])
owner = set([security.ROLE_OWNER])


class AgendaItemTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.agenda_item import AgendaItem
        return AgendaItem()

    def _make_proposal(self):
        from voteit.core.models.proposal import Proposal
        return Proposal()
    
    def _make_poll(self):
        from voteit.core.models.poll import Poll
        return Poll()

    def test_verify_implementation(self):
        from voteit.core.models.interfaces import IAgendaItem
        obj = self._make_obj()
        self.assertTrue(verifyObject(IAgendaItem, obj))

    def test_workflow_closed_state_marks_proposals_unhandled(self):
        """ Published proposals should be marked as 'unhandled' when
            an AI closes.
        """
        obj = self._make_obj()
        request = testing.DummyRequest()
        obj['proposal'] = self._make_proposal() #Should be published as initial state
        obj.set_workflow_state(request, 'inactive')
        obj.set_workflow_state(request, 'active')
        obj.set_workflow_state(request ,'closed')
        self.assertEqual(obj['proposal'].get_workflow_state(), u'unhandled')

    def test_workflow_closed_state_active_poll_exception(self):
        """ When you try to close an agenda items that has an ongoing
            poll in it, it should raise an exception.
        """
        request = testing.DummyRequest()
        obj = self._make_obj()

        obj['poll'] = self._make_poll()
        obj['poll'].set_workflow_state(request, 'planned')
        obj['poll'].set_workflow_state(request, 'ongoing')

        obj.set_workflow_state(request, 'inactive')
        obj.set_workflow_state(request, 'active')
        self.assertRaises(Exception, obj.set_workflow_state, 'closed')

    def test_timestamp_added_on_active(self):
        self.config.scan('voteit.core.subscribers.timestamps') #To add subscriber
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'inactive')
        self.assertFalse(isinstance(obj.start_time, datetime))
        obj.set_workflow_state(request, 'active')
        self.assertTrue(isinstance(obj.start_time, datetime))

    def test_timestamp_added_on_close(self):
        self.config.scan('voteit.core.subscribers.timestamps') #To add subscriber
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'inactive')
        obj.set_workflow_state(request, 'active')
        self.assertFalse(isinstance(obj.end_time, datetime))
        obj.set_workflow_state(request, 'closed')
        self.assertTrue(isinstance(obj.end_time, datetime))


class AgendaItemPermissionTests(unittest.TestCase):
    """ Check permissions in different agenda item states. """

    def setUp(self):
        self.config = testing.setUp()
        policy = ACLAuthorizationPolicy()
        self.pap = policy.principals_allowed_by_permission
        # load workflow
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.agenda_item import AgendaItem
        return AgendaItem()
    
    def _make_meeting(self):
        from voteit.core.models.meeting import Meeting
        return Meeting()

    def test_private(self):
        obj = self._make_obj()
        
        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator)
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)

        #Add proposal
        self.assertEqual(self.pap(obj, security.ADD_PROPOSAL), admin | moderator)

        #Add poll
        self.assertEqual(self.pap(obj, security.ADD_POLL), admin | moderator)

        #Add discussion post
        self.assertEqual(self.pap(obj, security.ADD_DISCUSSION_POST), admin | moderator)

        #Change workflow state
        self.assertEqual(self.pap(obj, security.CHANGE_WORKFLOW_STATE), admin | moderator)

    def test_active_with_closed_meeting(self):
        #FIXME: This workflow state combination should never happen with the current configuration of the site
        #We might want to remove this test, or change the raised exception so it happends on the workflow change instead.
        request = testing.DummyRequest()
        obj = self._make_obj()
        
        obj.set_workflow_state(request, 'inactive')
        obj.set_workflow_state(request, 'active')
        
        meeting = self._make_meeting()
        meeting.set_workflow_state(request, 'inactive')
        meeting.set_workflow_state(request, 'active')
        meeting.set_workflow_state(request, 'closed')
        
        meeting['ai'] = obj

        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | participant | viewer | owner)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), set())
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin)

        #Add proposal
        self.assertEqual(self.pap(obj, security.ADD_PROPOSAL), set())

        #Add poll
        self.assertEqual(self.pap(obj, security.ADD_POLL), set())

        #Add discussion post
        self.assertEqual(self.pap(obj, security.ADD_DISCUSSION_POST), set())

        #Change workflow state
        self.assertEqual(self.pap(obj, security.CHANGE_WORKFLOW_STATE), set())

    def test_active_with_active_meeting(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        
        obj.set_workflow_state(request, 'inactive')
        obj.set_workflow_state(request, 'active')
        
        meeting = self._make_meeting()
        meeting.set_workflow_state(request, 'inactive')
        meeting.set_workflow_state(request, 'active')
        
        meeting['ai'] = obj
        
        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant | owner)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator | owner)
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)

        #Add proposal
        self.assertEqual(self.pap(obj, security.ADD_PROPOSAL), admin | moderator | participant)

        #Add poll
        self.assertEqual(self.pap(obj, security.ADD_POLL), admin | moderator)

        #Add discussion post
        self.assertEqual(self.pap(obj, security.ADD_DISCUSSION_POST), admin | moderator | participant)

        #Change workflow state
        self.assertEqual(self.pap(obj, security.CHANGE_WORKFLOW_STATE), admin | moderator)

    def test_closed_ai_in_closed_meeting(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        
        obj.set_workflow_state(request, 'inactive')
        obj.set_workflow_state(request, 'active')
        obj.set_workflow_state(request, 'closed')
        
        meeting = self._make_meeting()
        meeting.set_workflow_state(request, 'inactive')
        meeting.set_workflow_state(request, 'active')
        meeting.set_workflow_state(request, 'closed')
        
        meeting['ai'] = obj
        
        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), set())
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), set())

        #Add proposal
        self.assertEqual(self.pap(obj, security.ADD_PROPOSAL), set())

        #Add poll
        self.assertEqual(self.pap(obj, security.ADD_POLL), set())

        #Add discussion post
        self.assertEqual(self.pap(obj, security.ADD_DISCUSSION_POST), set())

        #Change workflow state
        self.assertEqual(self.pap(obj, security.CHANGE_WORKFLOW_STATE), set())

    def test_closed_ai_in_open_meeting(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        
        obj.set_workflow_state(request, 'inactive')
        obj.set_workflow_state(request, 'active')
        obj.set_workflow_state(request, 'closed')
        
        meeting = self._make_meeting()
        meeting.set_workflow_state(request, 'inactive')
        meeting.set_workflow_state(request, 'active')
        
        meeting['ai'] = obj
        
        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), set())
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), set())

        #Add proposal
        self.assertEqual(self.pap(obj, security.ADD_PROPOSAL), set())

        #Add poll
        self.assertEqual(self.pap(obj, security.ADD_POLL), set())

        #Add discussion post
        self.assertEqual(self.pap(obj, security.ADD_DISCUSSION_POST), admin | moderator | participant)

        #Change workflow state
        self.assertEqual(self.pap(obj, security.CHANGE_WORKFLOW_STATE), admin | moderator)
