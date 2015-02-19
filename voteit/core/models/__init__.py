def includeme(config):
    """ Include all models. """
    config.include('.agenda_item')
    config.include('.agenda_template')
    config.include('.agenda_templates')
    config.include('.catalog')
    config.include('.date_time_util')
    config.include('.discussion_post')
    config.include('.fanstatic_resources')
    config.include('.flash_messages')
    config.include('.js_util')
    config.include('.logs')
    config.include('.meeting')
    config.include('.poll')
    config.include('.populator')
    config.include('.proposal')
    config.include('.proposal_ids')
    config.include('.site')
    config.include('.unread')
    config.include('.user')
    config.include('.user_tags')
    config.include('.users')
    config.include('.vote')
