import unittest

from pyramid import testing
from pyramid.httpexceptions import HTTPFound
from pyramid.security import authenticated_userid
from zope.interface import implementer
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from voteit.core.models.interfaces import IAuthPlugin
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.testing_helpers import bootstrap_and_fixture


@implementer(ISiteRoot)
class _DummyRoot(testing.DummyModel):
    pass


class AuthPluginTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.auth import AuthPlugin
        return AuthPlugin

    def _fixture(self):
        self.config.registry.registerAdapter(self._cut)
        root = bootstrap_and_fixture(self.config)
        request = testing.DummyRequest()
        return root, request

    def test_verify_class(self):
        self.assertTrue(verifyClass(IAuthPlugin, self._cut))

    def test_verify_obj(self):
        obj = self._cut(_DummyRoot(), testing.DummyRequest())
        self.assertTrue(verifyObject(IAuthPlugin, obj))

    def test_integration(self):
        self.config.registry.registerAdapter(self._cut)
        root = _DummyRoot()
        request = testing.DummyRequest()
        self.failUnless(self.config.registry.queryMultiAdapter((root, request), IAuthPlugin))

    def test_login(self):
        obj = self._cut(*self._fixture())
        self.assertRaises(NotImplementedError, obj.login, {})
