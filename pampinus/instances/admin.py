from django.contrib import admin

from instances.models import Instance, Server, Section, Master, Rack

admin.site.register(Instance)
admin.site.register(Server)
admin.site.register(Section)
admin.site.register(Master)
admin.site.register(Rack)
