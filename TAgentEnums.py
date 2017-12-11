class SessionTypeEnum(object):
    SESSION_TYPE_NONE = 0
    SESSION_TYPE_SERVER_UP = 1
    SESSION_TYPE_SERVER_DOWN = 2
    SESSION_TYPE_SENSOR = 3
    SESSION_TYPE_FRAMEWORKD = 4
    SESSION_TYPE_WEB = 5
    SESSION_TYPE_HA = 6
    SESSION_TYPE_ALL = 7


class PluginStateEnum(object):
    PLUGIN_IS_STARTED = 1
    PLUGIN_IS_STOPPED = 2


class SessionTypeStringEnum(object):
    SESSION_TYPE_SERVER = 'TServer'
    SESSION_TYPE_IDM = 'IDM'
    SESSION_TYPE_FRAMEWORKD = 'TFramework Daemon'