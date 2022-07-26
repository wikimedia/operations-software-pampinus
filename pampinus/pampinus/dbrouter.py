class DBRouter(object):

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'instances':
            return 'instances'
        # Returning None is no opinion, defer to other routers or default database
        return None

    def db_for_write(self, model, **hints):
        return self.db_for_read(model, **hints)
