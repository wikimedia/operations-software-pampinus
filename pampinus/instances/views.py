import re

from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.vary import vary_on_headers

from .models import Instance, Server, Section


@vary_on_headers('Accept')
def instance_list(request):
    search_query = request.GET.get('search', '').strip()
    instances = Instance.objects
    if search_query != '':
        for search in search_query.split(' '):
            if search.startswith('10.'):
                instances = instances.filter(version__startswith=search)
            elif search in ['master', 'primary']:
                instances = instances.exclude(master=None)
            elif search in ['slave', 'replica']:
                instances = instances.filter(master=None)
            elif search in [d[0] for d in Server.DCS]:
                instances = instances.filter(server__rack__dc=search)
            elif search in Section.objects.values_list('name', flat=True):
                instances = instances.filter(section__name=search) | instances.filter(section__name='test-' + search)
            elif search in [g[0] for g in Instance.INSTANCE_GROUPS]:
                instances = instances.filter(instance_group=search)
            elif len(search) == 2 and search[0] in 'ABCDEF' and search[1] in '123456789':
                instances = instances.filter(server__rack__name=search)
            else:
                instances = instances.filter(name__icontains=search)
    instances = instances.select_related('server')
    instances = instances.prefetch_related('section_set').prefetch_related('master_set')
    if request.accepts('application/json') and request.GET.get('format', 'application/json').strip() == 'json':
        instances = instances.order_by('-section__name', 'master__dc', 'name')
        return JsonResponse(list(instances.values()), safe=False)
    else:
        instances = instances.order_by('name')
        context = {'title': 'Instance list', 'instances': instances, 'search': search_query}
        return render(request, 'instances/list.html', context)


@vary_on_headers('Accept')
def instance_show(request, pk):
    instance = get_object_or_404(Instance, pk=pk)
    if request.accepts('application/json') and request.GET.get('format', 'application/json').strip() == 'json':
        return JsonResponse(model_to_dict(instance))
    else:
        context = {'title': f'Instance detail: {instance.name}', 'instance': instance,
                   'search': ''}
        return render(request, 'instances/show.html', context)


@vary_on_headers('Accept')
def server_list(request):
    search_query = request.GET.get('search', '').strip()
    servers = Server.objects
    if search_query != '':
        for search in search_query.split(' '):
            if search in Server.os_versions.keys():
                servers = servers.filter(os_version__startswith=Server.os_versions.get(search))
            elif search[0] in 'ABCDEF' and search[1] in '123456789':
                servers = servers.filter(rack__name=search)
            elif re.match(r'\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}', search):
                servers = servers.filter(ip=search)
            elif search in [d[0] for d in Server.DCS]:
                servers = servers.filter(rack__dc=search)
            else:
                servers = servers.filter(fqdn__startswith=search)
    if request.accepts('application/json') and request.GET.get('format', 'application/json').strip() == 'json':
        return JsonResponse(list(servers.values()), safe=False)
    else:
        servers = servers.order_by('fqdn').select_related('rack').prefetch_related('instance_set')
        context = {'title': 'Server list', 'servers': servers, 'search': search_query}
        return render(request, 'servers/list.html', context)


@vary_on_headers('Accept')
def server_show(request, hostname):
    server = get_object_or_404(Server, hostname=hostname)
    instances = server.instance_set.all()
    if request.accepts('application/json') and request.GET.get('format', 'application/json').strip() == 'json':
        return JsonResponse(model_to_dict(server))
    else:
        context = {'title': f'Server detail: {server.hostname}', 'server': server,
                   'instances': instances, 'search': ''}
        return render(request, 'servers/show.html', context)
