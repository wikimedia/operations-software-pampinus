from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404

from .models import Backup, Status


def backup_status(request):
    search_query = request.GET.get('search', '').strip()
    dc = 'all'
    section = 'all'
    backup_type = 'all'
    if search_query != '':
        for search in search_query.split(' '):
            if search in ['eqiad', 'codfw']:
                dc = search
            elif search in ['snapshot', 'dump']:
                backup_type = search
            elif search in Status.valid_sections():
                section = search
    status = Status.check_all_sections(dc=dc, section=section, backup_type=backup_type)
    context = {'title': 'Backup status', 'status': status, 'search': search_query}
    return render(request, 'dbbackups/status.html', context)


def backup_status_section(request, dc, section, backup_type):
    status_section = Status.check(dc, section, backup_type)
    backups = Backup.objects.extra(select={'is_ongoing': "status = 'ongoing'"})
    backups = backups.filter(host__icontains=dc).filter(type=backup_type).filter(section=section)
    backups = backups.order_by('-is_ongoing', '-pk')[:15]

    context = {'title': f'{status_section.backup_type} of {status_section.name} in {status_section.dc}',
               'status_section': status_section, 'search': '', 'backups': backups}
    return render(request, 'dbbackups/status_section.html', context)


def backup_list(request):
    search_query = request.GET.get('search', '').strip()
    backups = Backup.objects.extra(select={'is_ongoing': "status = 'ongoing'"})
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
    paginator = Paginator(backups, 50)
    page_number = request.GET.get('page')
    backups_page = paginator.get_page(page_number)
    context = {'title': 'Backup list', 'backups': backups_page,
               'num_backups_showed': len(backups_page), 'search': search_query}
    return render(request, 'dbbackups/list.html', context)


def backup_show(request, pk):
    backup = get_object_or_404(Backup, pk=pk)

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
