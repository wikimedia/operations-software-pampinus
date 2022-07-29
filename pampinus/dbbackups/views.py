import dateutil.parser
from django.core.paginator import Paginator
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.views.decorators.vary import vary_on_headers

from .models import Backup, Status


@vary_on_headers('Accept')
def backup_status(request):
    search_query = request.GET.get('search', '').strip()
    dc = request.GET.get('dc', 'all').strip()
    section = request.GET.get('section', 'all').strip()
    backup_type = request.GET.get('backup_type', 'all').strip()
    if search_query != '':
        for search in search_query.split(' '):
            if search in ['eqiad', 'codfw']:
                dc = search
            elif search in ['snapshot', 'dump']:
                backup_type = search
            elif search in Status.valid_sections():
                section = search
    status = Status.check_all_sections(dc=dc, section=section, backup_type=backup_type)
    if request.accepts('application/json') and request.GET.get('format', 'application/json').strip() == 'json':
        return JsonResponse([s.as_dict() for s in status], safe=False)
    else:
        context = {'title': 'Backup status', 'status': status, 'search': search_query}
        return render(request, 'dbbackups/status.html', context)


@vary_on_headers('Accept')
def backup_status_section(request, dc, section, backup_type):
    status_section = Status.check(dc, section, backup_type)
    backups = Backup.objects.extra(select={'is_ongoing': "status = 'ongoing'"})
    backups = backups.filter(host__icontains=dc).filter(type=backup_type).filter(section=section)
    backups = backups.order_by('-is_ongoing', '-pk')[:15]

    if request.accepts('application/json') and request.GET.get('format', 'application/json').strip() == 'json':
        return JsonResponse(status_section.as_dict())
    else:
        context = {'title': f'{status_section.backup_type} of {status_section.name} in {status_section.dc}',
                   'status_section': status_section, 'search': '', 'backups': backups}
        return render(request, 'dbbackups/status_section.html', context)


@vary_on_headers('Accept')
def backup_list(request):
    search_query = request.GET.get('search', '').strip()
    backups = Backup.objects.extra(select={'is_ongoing': "status = 'ongoing'"})
    before = request.GET.get('before', False)
    if before:
        try:
            date = dateutil.parser.parse(before)
        except dateutil.parser.ParserError:
            return HttpResponseBadRequest(f'Wrong parameter - before={before}')
        backups = backups.filter(end_date__lte=date)
    if search_query != '':
        for search in search_query.split(' '):
            if search in ['eqiad', 'codfw']:
                backups = backups.filter(host__icontains=search)
            elif search in [s[0] for s in Backup.status_list]:
                backups = backups.filter(status=search)
            elif search in [t[0] for t in Backup.type_list]:
                backups = backups.filter(type=search)
            elif search in Status.valid_sections():
                backups = backups.filter(section=search)
            else:
                backups = backups.filter(name__icontains=search)
    backups = backups.order_by('-is_ongoing', '-pk')

    if request.accepts('application/json') and request.GET.get('format', 'application/json').strip() == 'json':
        backups = backups[:50].values()
        return JsonResponse(list(backups), safe=False)
    else:
        paginator = Paginator(backups, 50)
        page_number = request.GET.get('page')
        backups_page = paginator.get_page(page_number)
        context = {'title': 'Backup list', 'backups': backups_page,
                   'num_backups_showed': len(backups_page), 'search': search_query}
        return render(request, 'dbbackups/list.html', context)


@vary_on_headers('Accept')
def backup_show(request, pk):
    backup = get_object_or_404(Backup, pk=pk)
    if request.accepts('application/json') and request.GET.get('format', 'application/json').strip() == 'json':
        return JsonResponse(model_to_dict(backup))
    else:
        search_query = request.GET.get('search', '').strip()
        files = backup.file_set.all()
        if search_query != '':
            for search in search_query.split(' '):
                files = files.filter(Q(file_path__icontains=search) |
                                     Q(file_name__icontains=search))
        files = files.order_by('pk')
        paginator = Paginator(files, 50)
        page_number = request.GET.get('page')
        files_page = paginator.get_page(page_number)

        context = {'title': f'Backup detail: {backup.name}', 'backup': backup,
                   'files': files_page, 'num_files_showed': len(files_page),
                   'search': search_query}
        return render(request, 'dbbackups/show.html', context)
