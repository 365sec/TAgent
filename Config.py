from optparse import OptionParser

import os
import sys
import re
import codecs


from optparse import OptionParser

from syslog_log import *


class Conf(ConfigParser):
    OPTCRE = re.compile('(?P<option>[^:=\\s][^=]*)\\s*(?P<vi>[:=])\\s*(?P<value>.*)$')

    def read(self, filenames, encoding = 'latin1', check_neededEntries = True):
        self.__validConfig = True
        fp = None
        for filename in filenames:
            if not os.path.isfile(filename):
                print('Configuration file (%s) does not exist!' % filename)
            try:
                fp = codecs.open(filename, 'r', encoding=encoding)
                self.readfp(fp)
                fp.close()
            except Exception as e:
                self.__validConfig = False

   


    def _strip_value(self, value):
        from string import strip
        return strip(strip(value, '"'), "'")

    def hitems(self, section, braw = False):
        hash = {}
        for item in self.items(section, braw):
            hash[item[0]] = self._strip_value(item[1])

        return hash

    def get(self, section, option):
        try:
            value = ConfigParser.get(self, section, option)
            value = self._strip_value(value)
        except:
            value = ''

        return value

    def getboolean(self, section, option):
        try:
            value = ConfigParser.getboolean(self, section, option)
        except ValueError:
            return False

        return value

    def __repr__(self):
        conf_str = '<sensor-config>\n'
        for section in sorted(self.sections()):
            conf_str += '  <section name="%s">\n' % section
            for i in self.items(section):
                conf_str += '    <item name="%s" value="%s" />\n' % (i[0], i[1])

            conf_str += '  </section>\n'

        conf_str += '</sensor-config>'
        return conf_str
    

class CommandLineOptions:

    def __init__(self):
        self.__options = None
        parser = OptionParser(usage='%prog [-v] [-q] [-d] [-f] [-g] [-c config_file]', version='OSSIM (Open Source Security Information Management) ' + '- Agent ')
        parser.add_option('-v', '--verbose', dest='verbose', action='count', help='verbose mode, makes lot of noise')
        parser.add_option('-d', '--daemon', dest='daemon', action='store_true', help='Run agent in daemon mode')
        parser.add_option('-f', '--force', dest='force', action='store_true', help='Force startup overriding pidfile')
        parser.add_option('-s', '--stats', dest='stats', type='choice', choices=['all', 'clients', 'plugins'], default=None, help='Get stats about the agent')
        parser.add_option('-c', '--config', dest='config_file', action='store', help='read config from FILE', metavar='FILE')
        self.__options, args = parser.parse_args()
        if len(args) > 1:
            parser.error('incorrect number of arguments')
        if self.__options.verbose and self.__options.daemon:
            parser.error('incompatible options -v -d')

    def get_options(self):
        return self.__options
    
    
if __name__  == "__main__":
    print "you "
    config = Conf()
    
    config.read([os.path.join(os.path.dirname(os.path.realpath(__file__)),"config.cfg")])
    print config.get("log","verbose")
    print config.get("server","ip")
    print config.get("server","port")