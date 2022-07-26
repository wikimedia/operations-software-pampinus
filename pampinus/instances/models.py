from django.db import models

wmf_datacenters = [
    ('eqiad', 'eqiad (db1XXX)'),
    ('codfw', 'codfw (db2XXX)'),
    ('esams', 'esams (db3XXX)'),
    ('ulsfo', 'ulsfo (db4XXX)'),
    ('eqsin', 'eqsin (db5XXX)'),
    ('drmrs', 'drmrs (db6XXX)')
]


class Rack(models.Model):
    "Racks (have specific id on netbox"

    class Meta:
        unique_together = (('name', 'dc'),)
        db_table = 'racks'

    name = models.CharField(max_length=5,
                            help_text="Rack name.")
    identifier = models.IntegerField(primary_key=True,
                                     help_text="Rack identifier on Netbox")
    dc = models.CharField(max_length=100,
                          choices=wmf_datacenters,
                          help_text="Datacenter where the rack is physically located")

    def __str__(self):
        return f'{self.name} ({self.dc})'


class Server(models.Model):
    """Physical or virtual server."""

    DCS = wmf_datacenters
    os_versions = {
        'jessie': '8',
        'stretch': '9',
        'buster': '10',
        'bullseye': '11',
        'bookworm': '12',
        'trixie': '13',
    }

    class Meta:
        db_table = 'servers'

    fqdn = models.CharField(max_length=300,
                            primary_key=True,
                            help_text="Fully qualified domain name a physical or "
                                      "virtual linux server.")
    hostname = models.CharField(max_length=100,
                                db_index=True,
                                help_text="Hostname of the server.")
    rack = models.ForeignKey(Rack,
                             on_delete=models.SET_NULL,
                             null=True,
                             blank=True,
                             help_text="Netbox identifier where the server "
                                       "is physically located within the "
                                       "datacenter.")

    ip = models.GenericIPAddressField(null=True,
                                      blank=True,
                                      help_text="IP address (v4 or v6) of the server")
    os_version = models.CharField(max_length=100,
                                  null=True,
                                  blank=True,
                                  help_text="String representing the operating "
                                            "system version of the server (e.g. 11.5)")
    last_boot = models.DateTimeField(null=True,
                                     blank=True,
                                     help_text="Timestamp of when the server "
                                               "last booted up, to track "
                                               "its uptime.")

    def __str__(self):
        return self.fqdn


class Instance(models.Model):
    """MySQL server instance."""
    INSTANCE_GROUPS = [
        ('core', 'MediaWiki Core Server that will serve production traffic'),
        ('misc', 'Miscelaneous DB (Phab, bacula, etherpad, zarcillo)'),
        ('dbstore', 'Backup source or analytics servers (dbstore)'),
        ('parsercache', 'MediaWiki Parser Cache'),
        ('cloud', 'CloudDB (formerly, labsdb)'),
        ('test', 'Test Server')]

    class Meta:
        db_table = 'instances'

    name = models.CharField(max_length=300,
                            primary_key=True,
                            help_text="The name of the mysql instance.")
    server = models.ForeignKey(Server,
                               on_delete=models.CASCADE,
                               help_text="The name of the server where the "
                                         "instance lives.")
    port = models.IntegerField(help_text="The main port number where the "
                                         "instance listens to incoming "
                                         "connections.")
    instance_group = models.CharField(max_length=30,
                                      choices=INSTANCE_GROUPS,
                                      help_text=("Basic group the instance belongs to"))
    version = models.CharField(max_length=100,
                               null=True,
                               blank=True,
                               help_text="The version of the server running "
                                         "in that instance.")
    last_start = models.DateTimeField(null=True,
                                      blank=True,
                                      help_text="Timestamp of when the instance "
                                                "last started running, to track "
                                                "its uptime.")

    def __str__(self):
        return self.name


class Section(models.Model):
    """MySQL sections (replica sets)"""

    REPLICATION_GROUPS = [
        ('mw', 'MediaWiki'),
        ('test', 'Test'),
        ('analytics', 'Data Engineering'),
        ('misc', 'Miscelaneous'),
        ('cloud', 'WMF Cloud')]

    class Meta:
        db_table = 'sections'

    name = models.CharField(max_length=30,
                            primary_key=True,
                            help_text="Section identifier")
    replication_group = models.CharField(max_length=30,
                                         choices=REPLICATION_GROUPS)
    standalone = models.BooleanField(default=False)

    instances = models.ManyToManyField(Instance, db_table='section_instances')

    def __str__(self):
        return self.name


class Master(models.Model):
    """Replication primary instances on each dc"""

    class Meta:
        unique_together = (('section', 'dc'),)
        db_table = 'masters'

    dc = models.CharField(max_length=100,
                          choices=Server.DCS,
                          help_text="Datacenter in which the instance is "
                                    "a primary server.")
    instance = models.ForeignKey(Instance,
                                 on_delete=models.RESTRICT,
                                 help_text="Instance name that is the "
                                           "primary one on given DC.")
    section = models.ForeignKey(Section,
                                on_delete=models.CASCADE,
                                help_text="Reference to a section "
                                          "(replica set) name.")

    def __str__(self):
        return f'{self.section.name} ({self.dc})'
