from copy import deepcopy

from sqlalchemy import Column, VARCHAR, TEXT, INT, SMALLINT
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class ReprMixin(object):
    key_order = None
    def __repr__(self):
        return '<%s>' % self.__class__.__name__

    def to_dict(self):
        _dict = deepcopy(self.__init__)
        _dict.pop('_sa_instance_state')
        return _dict

class Record(Base, ReprMixin):
    __tablename__ = 'records'

    id = Column('id', INT, primary_key=True)
    domain_id = Column('domain_id', INT)
    name = Column('name', VARCHAR(255))
    type = Column('type', VARCHAR(6))
    content = Column('content', VARCHAR(255))
    ttl = Column('ttl', INT)
    prio = Column('prio', INT)
    change_date = Column('change_date', INT)

    key_order = ('type', 'name', 'content', 'change_date', 'ttl', 'id', 'domain_id', 'prio')

    def __init__(self, id, domain_id, name, type, content, ttl=3600, prio=0, change_date=0):
        self.id = id
        self.domain_id = domain_id
        self.name = name
        self.type = type
        self.content = content
        self.ttl = ttl
        self.prio = prio
        self.change_date = change_date

    def __repr__(self):
        return '<%s(%s: Name: %s <=> Content: %s)>' % (self.__class__.__name__, self.type, self.name, self.content)


class Domain(Base, ReprMixin):
    __tablename__ = 'domains'
    
    id = Column('id', INT, primary_key=True)
    name = Column('name', VARCHAR(255))
    master = Column('master', VARCHAR(255))
    last_check = Column('last_check', INT)
    type = Column('type', VARCHAR(255))
    notified_serial = Column('notified_serial', INT)
    account = Column('account', VARCHAR(40))

    def __init__(self, id, name, master=None, last_check=None, type='MASTER', notified_serial=None, account=None):
        self.id = id
        self.name = name
        self.master = master
        self.last_check = last_check
        self.type = type
        self.notified_serial = notified_serial
        self.account = account

    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, self.name )

class SuperMaster(Base, ReprMixin):
    __tablename__ = 'supermasters'

    ip = Column('ip', VARCHAR(25), primary_key=True)
    nameserver = Column('nameserver', VARCHAR(255), primary_key=True)
    account = Column('account', VARCHAR(40), primary_key=True)

    def __init__(self, ip, nameserver, account):
        self.ip = ip
        self.nameserver = nameserver
        self.account = account

class Zone(Base, ReprMixin):
    __tablename__ = 'zones'

    id = Column('id', INT, primary_key=True)
    domain_id = Column('domain_id', INT)
    owner = Column('owner', INT)
    content = Column('comment', TEXT)
    zone_templ_id = Column('zone_templ_id', INT)

    def __init__(self, id, domain_id, owner, content, zone_templ_id):
        self.id = id
        self.domain_id = domain_id
        self.owner = owner
        self.content = content
        self.zone_templ_id = zone_templ_id


class ZoneTemplate(Base, ReprMixin):
    __tablename__ = 'zone_templ'

    id = Column('id', INT, primary_key=True)
    name = Column('name', VARCHAR(128))
    descr = Column('descr', TEXT)
    owner = Column('owner', INT)

    def __init__(self, id, name, owner):
        self.id = id
        self.name = name
        self.owner = owner


class ZoneTemplateRecords(Base, ReprMixin):
    __tablename__ = 'zone_templ_records'

    id = Column('id', INT, primary_key=True)
    zone_templ_id = Column('zone_templ_id', INT)
    name = Column('name', VARCHAR(255))
    type = Column('type', VARCHAR(6))
    content = Column('content', VARCHAR(255))
    ttl = Column('ttl', INT)
    prio = Column('prio', INT)

    def __init__(self, id, zone_templ_id, name, type, content, ttl, prio):
        self.id = id
        self.zone_templ_id = zone_templ_id
        self.name = name
        self.type = type
        self.content = content
        self.ttl = ttl
        self.prio = prio


class PermTemplate(Base, ReprMixin):
    __tablename__ = 'perm_templ'

    id = Column('id', INT, primary_key=True)
    name = Column('name', VARCHAR(128))
    descr = Column('descr', TEXT)

    def __init__(self, id, name, descr):
        self.id = id
        self.name = name
        self.descr = descr


class PermItem(Base, ReprMixin):
    __tablename__ = 'perm_items'
    id = Column('id', INT, primary_key=True)
    name = Column('name', VARCHAR(64))
    descr = Column('descr', TEXT)

    def __init__(self, id, name, descr):
        self.id = id
        self.name = name
        self.descr = descr


class User(Base, ReprMixin):
    __tablename__ = 'users'
    id = Column('id', INT, primary_key=True)
    username = Column('username', VARCHAR(16))
    password = Column('password', VARCHAR(34))
    fullname = Column('fullname', VARCHAR(255))
    email = Column('email', VARCHAR(255))
    description = Column('description', TEXT)
    active = Column('active', SMALLINT)

    def __init__(self, id, username, password, fullname, email, description, active):
        self.id = id
        self.username = username
        self.password = password
        self.fullname = fullname
        self.email = email
        self.description = description
        self.active = active


class PermTemplateItem(Base, ReprMixin):
    __tablename__ = 'perm_templ_items'

    id = Column('id', INT, primary_key=True)
    templ_id = Column('templ_id', INT)
    perm_id = Column('perm_id', INT)

    def __init__(self, id, templ_id, perm_id):
        self.id = id
        self.templ_id = templ_id
        self.perm_id = perm_id
