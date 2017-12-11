from optparse import OptionParser




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