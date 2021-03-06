from voteit.core import VoteITMF as _
from voteit.core.models.arche_compat import createContent
from voteit.core.security import ROLE_ADMIN


def bootstrap_voteit(echo=True):
    """ Bootstrap site root.
        Will add:
        - Site root
        - Agenda template folder
        - Users folder
        - An administrative user with login: admin and pass: admin
    """
    if echo:
        print "Bootstrapping site - creating 'admin' user with password 'admin'"
    #Add root
    root = createContent('Root', title = _(u"VoteIT"), creators = ['admin'])
    root.set_field_value('footer', u'<a href="http://www.voteit.se">www.voteit.se</a> &mdash; '
                                   u'<a href="http://manual.voteit.se">User and developer manual</a> &mdash; '
                                   u'<a href="https://github.com/VoteIT">Source code and bugtracker</a>')
    #Add templates if available
    try:
        root['agenda_templates'] = createContent('AgendaTemplates',
                                                 title = _(u"Agenda templates"),
                                                 creators = ['admin'])
    except KeyError:
        pass #For tests etc
    #Add users folder
    root['users'] = createContent('Users', title = _(u"Registered users"), creators = ['admin'])
    users = root.users
    #Add user admin - note that creators also set owner, which is important for changing password
    admin = createContent('User',
                          password = 'admin',
                          creators = ['admin'],
                          first_name = _(u'VoteIT'),
                          last_name = _(u'Administrator'))
    users['admin'] = admin
    #Add admin to group managers
    root.add_groups('admin', [ROLE_ADMIN])
    return root
