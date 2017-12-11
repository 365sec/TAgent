# Embedded file name: ossim-agent/syslog_log.py
import syslog
import CommonVariables
from ConfigParser import ConfigParser

__g_verbose = None
__g_debug_levels = ['debug']
__g_info_levels = ['debug', 'info']
__g_warning_levels = ['debug', 'info', 'warning']
__g_error_levels = ['debug',
 'info',
 'warning',
 'error']
__g_critical_levels = ['debug',
 'info',
 'warning',
 'error',
 'critical']

def read_verbose_info():
    global __g_verbose
    config = ConfigParser()
    config_file = open(CommonVariables.DEFAULT_CONFIG_FILE, 'r')
    if config and config_file:
        config.readfp(config_file)
        config_file.close()
        __g_verbose = config.get('log', 'verbose')
    if __g_verbose not in __g_critical_levels:
        __g_verbose = 'info'


def debug(message):
    if __g_verbose is None:
        read_verbose_info()
    if __g_verbose in __g_debug_levels:
        try:
            print "debug " + message
            syslog.syslog(syslog.LOG_DEBUG, 'Alienvault-Agent[DEBUG]: ' + message)
        except:
            pass

    return


def info(message):
    if __g_verbose is None:
        read_verbose_info()
    if __g_verbose in __g_info_levels:
        try:
            print "info " + message
            syslog.syslog(syslog.LOG_INFO, 'Alienvault-Agent[INFO]: ' + message)
        except:
            pass

    return


def warning(message):
    if __g_verbose is None:
        read_verbose_info()
    if __g_verbose in __g_warning_levels:
        try:
            print "error " + message
            syslog.syslog(syslog.LOG_WARNING, 'Alienvault-Agent[WARNING]: ' + message)
        except:
            pass

    return


def error(message):
    if __g_verbose is None:
        read_verbose_info()
    if __g_verbose in __g_error_levels:
        try:
            print "error " + message
            syslog.syslog(syslog.LOG_ERR, 'Alienvault-Agent[ERROR]: ' + message)
        except:
            pass

    return


def critical(message):
    if __g_verbose is None:
        read_verbose_info()
    if __g_verbose in __g_critical_levels:
        try:
            print "critical " + message
            syslog.syslog(syslog.LOG_CRIT, 'Alienvault-Agent[CRITICAL]: ' + message)
        except:
            pass

    return


if __name__ == "__main__":
    while True:
      warning( "ok!")
      syslog.syslog(syslog.LOG_CRIT, 'Alienvault-Agent[CRITICAL]: ' + "shaochuyueh")
      
 