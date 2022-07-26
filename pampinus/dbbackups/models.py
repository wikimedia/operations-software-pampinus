import datetime

from django.utils import timezone
from django.db import models
from django.template.defaultfilters import filesizeformat

from wmfbackups import WMFMetrics


class Backup(models.Model):
    status_list = [
        ('ongoing', 'backup is ongoing'),
        ('finished', 'backup finished sucessfully'),
        ('failed', 'backup terminated with errors')
    ]
    type_list = [
        ('dump', 'logical dump'),
        ('snapshot', 'snapshot')
    ]

    class Meta:
        db_table = 'backups'

    @property
    def duration(self):
        if self.end_date is None or self.start_date is None:
            return None
        return self.end_date - self.start_date

    name = models.CharField(max_length=100,
                            help_text="Complete name of the backup job.")
    status = models.CharField(max_length=10,
                              choices=status_list,
                              help_text="Status of the backup (ongoing, etc.).")
    source = models.CharField(max_length=100,
                              help_text="Instance, source of the backup, in "
                                        "host:port format.")
    host = models.CharField(max_length=300,
                            help_text="Host where the backup was sent/was stored.")
    type = models.CharField(max_length=10,
                            choices=type_list,
                            help_text="Type of backup generated")
    section = models.CharField(max_length=100,
                               help_text="Section name or general identifiery for "
                                         "the job (s1, tendril, etc.)")
    start_date = models.DateTimeField(null=True,
                                      blank=True,
                                      help_text="Timestamp of when the backup started.")
    end_date = models.DateTimeField(null=True,
                                    blank=True,
                                    help_text="Timestamp of when the backup finished.")
    total_size = models.BigIntegerField(null=True,
                                        blank=True,
                                        help_text="Total size of the backup after completion.")

    def __str__(self):
        return str(self.name)


class Status:
    percentage_change_warning = 5.0
    percentage_change_alert = 15.0
    min_size = 300 * 1024
    sections_to_check = {
        's1': {'snapshot': 2, 'dump': 8},
        's2': {'snapshot': 2, 'dump': 8},
        's3': {'snapshot': 2, 'dump': 8},
        's4': {'snapshot': 2, 'dump': 8},
        's5': {'snapshot': 2, 'dump': 8},
        's6': {'snapshot': 2, 'dump': 8},
        's7': {'snapshot': 2, 'dump': 8},
        's8': {'snapshot': 2, 'dump': 8},
        'x1': {'snapshot': 2, 'dump': 8},
        'es1': {'dump': 1095, 'readonly': True},
        'es2': {'dump': 1095, 'readonly': True},
        'es3': {'dump': 1095, 'readonly': True},
        'es4': {'dump': 8},
        'es5': {'dump': 8},
        'm1': {'dump': 8},
        'm2': {'dump': 8},
        'm3': {'dump': 8},
        'm5': {'dump': 8},
        'db_inventory': {'dump': 8}
    }
    datacenters_to_check = ['eqiad', 'codfw']

    state_list = [
        ('missing', 'There is no completed backup found, not even an old one'),
        ('stale', 'There is a backup, but it is older than the expected configured freshness'),
        ('very_stale', 'There is a backup, but it is older than 2 times the expected configured freshness'),
        ('wrong_size', 'The backup size changed noticeably compared to the previous backup'),
        ('very_wrong_size', 'The backup is too small, or it changed a lot compared to the previous backup'),
        ('only_one', 'There is only one backup, so we cannot compare it size'),
        ('fresh', 'There is a backup that finished correctly and has the right size')
    ]

    def __init__(self, dc, name, backup_type, state, msg=None, state_description=None,
                 start_date=None, end_date=None, job=None, last_job=None,
                 duration=None, size=None, size_change_percentage=None):
        self.dc = dc
        self.name = name
        self.backup_type = backup_type
        self.state = state
        self.state_description = state_description
        self.start_date = start_date
        self.end_date = end_date
        self.size = size
        self.size_change_percentage = size_change_percentage
        self.msg = msg
        self.job = job
        self.last_job = last_job
        self.duration = duration

    @staticmethod
    def check_all_sections(dc='all', section='all', backup_type='all'):
        if dc == 'all':
            dcs = Status.datacenters_to_check
        else:
            dcs = [dc]
        if section == 'all':
            sections = Status.sections_to_check.keys()
        else:
            sections = [section]
        status = []
        if backup_type == 'all':
            backup_types = [t[0] for t in Backup.type_list]
        else:
            backup_types = [backup_type]

        for s in sections:
            for dc in dcs:
                properties = Status.sections_to_check.get(s)
                if properties is not None:
                    for backup_type in properties.keys():
                        if backup_type in backup_types:
                            status.append(Status.check(dc, s, backup_type))
        return status

    @staticmethod
    def valid_sections():
        """Returns a list of valid sections from configuration"""
        return WMFMetrics.WMFMetrics.get_valid_sections()

    @staticmethod
    def check(dc, section, backup_type):
        # list of completed backups
        results = Backup.objects.filter(host__icontains=dc).filter(section=section).filter(type=backup_type)
        results = results.filter(status='finished').exclude(end_date__isnull=True)
        results = results.order_by('-start_date')[:2]

        # list of ongoing/failed ones
        last_jobs = Backup.objects.filter(host__icontains=dc).filter(section=section).filter(type=backup_type)
        last_jobs = last_jobs.exclude(status='finished')
        last_jobs = last_jobs.order_by('-start_date')[:1]
        last_job = last_jobs[0] if (len(last_jobs) > 0 and
                                    len(results) > 0 and
                                    last_jobs[0].start_date > results[0].start_date) else None

        state_descriptions = {i[0]: i[1] for i in Status.state_list}
        if len(results) == 0:
            return Status(dc=dc, name=section, backup_type=backup_type, duration=None, state='missing',
                          msg='No backup found', state_description=state_descriptions.get('missing'),
                          last_job=last_job)
        result = results[0]
        print(result.start_date, result.end_date)
        expected_freshness = Status.sections_to_check[section][backup_type]
        # very stale
        if result.start_date < (
            timezone.now() - datetime.timedelta(days=expected_freshness * 2)
        ):
            return Status(dc=dc, name=section,
                          backup_type=result.type, duration=result.duration, state='very_stale',
                          msg=f'Last backup taken more than {expected_freshness} days ago, '
                              'double the expected age.',
                          state_description=state_descriptions.get('very_stale'),
                          start_date=result.start_date, end_date=result.end_date,
                          job=result.id, last_job=last_job, size=result.total_size)

        # stale
        if result.start_date < (
            timezone.now() - datetime.timedelta(days=expected_freshness)
        ):
            return Status(dc=dc, name=section,
                          backup_type=result.type, duration=result.duration, state='stale',
                          msg=f'Last backup taken more than {expected_freshness} days ago.',
                          state_description=state_descriptions.get('stale'),
                          start_date=result.start_date, end_date=result.end_date,
                          job=result.id, last_job=last_job, size=result.total_size)
        # too small
        if result.total_size < Status.min_size:
            return Status(dc=dc, name=section,
                          backup_type=result.type, duration=result.duration, state='wrong_size',
                          msg=f'Backup is {filesizeformat(result.size)} bytes, '
                              f'less than the expected minimum size: {Status.min_size}.',
                          state_description=state_descriptions.get('wrong_size'),
                          start_date=result.start_date, end_date=result.end_date,
                          job=result.id, last_job=last_job, size=result.total_size)

        # only one
        if not Status.sections_to_check.get(section).get('readonly') and len(results) < 2:
            return Status(dc=dc, name=section,
                          backup_type=result.type, duration=result.duration, state='only_one',
                          state_description=state_descriptions.get('only_one'),
                          msg='There is only one backup available, so we cannot compare its size.',
                          start_date=result.start_date, end_date=result.end_date,
                          job=result.id, last_job=last_job, size=result.total_size)
        if len(results) >= 2:
            previous = results[1]
            percentage_change = (result.total_size - previous.total_size) / previous.total_size * 100.0
            # critical size
            if abs(percentage_change) >= Status.percentage_change_alert:
                return Status(dc=dc, name=section,
                              backup_type=result.type, state='very_wrong_size',
                              msg=f'The previous backup had a size of {filesizeformat(previous.total_size)}, '
                                  f'a change larger than {Status.percentage_change_alert}%.',
                              state_description=state_descriptions.get('very_wrong_size'),
                              start_date=result.start_date, end_date=result.end_date,
                              duration=result.duration,
                              job=result.id, last_job=last_job, size=result.total_size,
                              size_change_percentage=percentage_change)

            if abs(percentage_change) >= Status.percentage_change_warning:
                return Status(dc=dc, name=section,
                              backup_type=result.type, state='wrong_size',
                              msg=f'The previous backup had a size of {filesizeformat(previous.total_size)}, '
                                  f'a change larger than {Status.percentage_change_warning}%.',
                              state_description=state_descriptions.get('wrong_size'),
                              start_date=result.start_date, end_date=result.end_date,
                              duration=result.duration,
                              job=result.id, last_job=last_job, size=result.total_size,
                              size_change_percentage=percentage_change)
            # fresh backups
            return Status(dc=dc, name=section,
                          backup_type=result.type, state='fresh',
                          msg='',
                          state_description=state_descriptions.get('fresh'),
                          start_date=result.start_date, end_date=result.end_date,
                          duration=result.duration,
                          job=result.id, last_job=last_job, size=result.total_size,
                          size_change_percentage=percentage_change)

        # readonly host with 1 backup
        return Status(dc=dc, name=section,
                      backup_type=result.type, state='fresh',
                      msg='',
                      state_description=state_descriptions.get('fresh'),
                      start_date=result.start_date, end_date=result.end_date,
                      duration=result.duration,
                      job=result.id, last_job=last_job, size=result.total_size,
                      size_change_percentage='-')


class Object(models.Model):
    """
    Generic representation of production database objects: tables,
    databases, triggers, views, etc.
    """
    class Meta:
        db_table = 'backup_objects'
        unique_together = (('backup_id', 'db', 'name'),)

    backup = models.ForeignKey(Backup,
                               on_delete=models.CASCADE,
                               help_text="Reference to a backup job.")
    db = models.CharField(max_length=100,
                          help_text="Name of the database this object belongs to.")
    name = models.CharField(max_length=100,
                            help_text="Name of the object.")
    size = models.BigIntegerField(help_text="Size, in bytes, of the object.")


class File(models.Model):

    class Meta:
        db_table = 'backup_files'
        unique_together = (('backup_id', 'file_path', 'file_name'),)

    backup = models.ForeignKey(Backup,
                               on_delete=models.CASCADE,
                               help_text="Reference to a backup job.")
    file_path = models.CharField(max_length=300,
                                 help_text="Path of the parent directory, empty string "
                                           "if it is a top-level file or directory")
    file_name = models.CharField(max_length=300,
                                 help_text="Base name of the file")
    size = models.BigIntegerField(help_text="Size, in bytes, of the file.")
    file_date = models.DateTimeField(null=True,
                                     blank=True,
                                     help_text="File's last modified atribute.")
    backup_object = models.ForeignKey(Object,
                                      null=True,
                                      blank=True,
                                      on_delete=models.SET_NULL,
                                      help_text="Reference to a production file.")

    def __str__(self):
        return self.backup + ':' + self.file_path + '/' + self.file_name
