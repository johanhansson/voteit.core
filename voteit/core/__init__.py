from pyramid.i18n import TranslationStringFactory
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from repoze.zodbconn.finder import PersistentApplicationFinder
from pyramid.config import Configurator
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.authentication import AuthTktAuthenticationPolicy


#Must be before all of this packages imports since some other methods might import it
PROJECTNAME = 'voteit.core'
VoteITMF = TranslationStringFactory(PROJECTNAME)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    import voteit.core.patches
    from voteit.core import app
    from voteit.core.security import groupfinder

    #Authentication policies
    authn_policy = AuthTktAuthenticationPolicy(secret=settings['tkt_secret'],
                                               callback=groupfinder)
    authz_policy = ACLAuthorizationPolicy()

    zodb_uri = settings.get('zodb_uri')
    if zodb_uri is None:
        raise ValueError("No 'zodb_uri' in application configuration.")

    finder = PersistentApplicationFinder(zodb_uri, appmaker)
    def get_root(request):
        return finder(request.environ)

    sessionfact = UnencryptedCookieSessionFactoryConfig('messages')

    
    config = Configurator(settings=settings,
                          authentication_policy=authn_policy,
                          authorization_policy=authz_policy,
                          root_factory=get_root,
                          session_factory = sessionfact,)
    
    #FIXME: Pluggable startup procedure?
    app.register_poll_plugins(config)
    
    #Component includes
    config.include('voteit.core.models.user_tags')
    config.include('voteit.core.models.logs')
    config.include('voteit.core.models.date_time_util')
    config.include('voteit.core.models.catalog')
    config.include('voteit.core.models.export_import')
    #For password storage
    config.scan('betahaus.pyracont.fields.password')
    
    
    config.add_static_view('static', '%s:static' % PROJECTNAME)
    config.add_static_view('deform', 'deform:static')

    #Set which mailer to use
    config.include(settings['mailer'])

    config.add_translation_dirs('deform:locale/',
                                'colander:locale/',
                                '%s:locale/' % PROJECTNAME,)

    config.scan(PROJECTNAME)

    config.hook_zca()
    
    return config.make_wsgi_app()


def appmaker(zodb_root):
    if not 'app_root' in zodb_root:
        from voteit.core.bootstrap import bootstrap_voteit
        zodb_root['app_root'] = bootstrap_voteit() #Returns a site root
        import transaction
        transaction.commit()
    return zodb_root['app_root']
