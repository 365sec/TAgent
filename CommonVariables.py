#Embedded file name: ossim-agent/CommonVariables.py
OUTPUT_SERVER_LIST_REGEXP = '(?P<server_ip>(?:[\\d]{1,3})\\.(?:[\\d]{1,3})\\.(?:[\\d]{1,3})\\.(?:[\\d]{1,3}))\\|(?P<server_port>[0-9]{1,5})\\|(?P<server_priority>[0-5])\\|(?P<frmk_ip>(?:[\\d]{1,3})\\.(?:[\\d]{1,3})\\.(?:[\\d]{1,3})\\.(?:[\\d]{1,3}))\\|(?P<frmk_port>[0-9]{1,5})'
GET_FRAMEWORK_DATA_REGEXP = 'server_ip="(?P<srv_ip>(?:[\\d]{1,3})\\.(?:[\\d]{1,3})\\.(?:[\\d]{1,3})\\.(?:[\\d]{1,3}))" server_name="(?P<srv_name>([^"]+))" server_port="(?P<srv_port>\\d+)" framework_ip="(?P<frmk_ip>(?:[\\d]{1,3})\\.(?:[\\d]{1,3})\\.(?:[\\d]{1,3})\\.(?:[\\d]{1,3}))" framework_name="(?P<frmk_name>([^"]+))" framework_port="(?P<frmk_port>\\d+)"'
OUTPUT_SERVER_IP_TOKEN = 'server_ip'
OUTPUT_SERVER_PORT_TOKEN = 'server_port'
OUTPUT_SERVER_PRIORITY_TOKEN = 'server_priority'
OUTPUT_FRAMEWORK_IP_TOKEN = 'frmk_ip'
OUTPUT_FRAMEWORK_PORT_TOKEN = 'frmk_port'
OUTPUT_SERVER_LIST_SECTION = 'output-server-list'
SDEE_DATA_FILE = '/etc/ossim/agent/sdee_sid.data'
DEFAULT_CONFIG_FILE = '/etc/ossim/agent/config.cfg'
DEFAULT_TEST_CONFIG_FILE = '/home/crosa/workspace/MP-agent/src/etc/agent/config.cfg'
SERVER_DEFAULT_PORT = 40001
FRAMEWORK_DEFAULT_PORT = 40003
TIME_TO_CHECK_SERVER_LIST = 60
TIME_TO_MANAGE_SERVER_CHANGE = 300
CHECK_ALIVE_TIME_INTERVAL = 60
MAX_PRIORITY_VALUE = 5
MAX_SERVER_BREAKS_COUNTER = 2
COMMUNICATION_BASE_DIR = '/var/ossim/agent_conn/'
WATCHDOG_UNIX_SOCKET = '/var/ossim/agent_conn/wd_socket'
STATS_UNIX_SOCKET = '/var/ossim/agent_conn/stats_socket'
LOG_UNIX_SOCKET = '/var/ossim/agent_conn/log_socket'
EVENTS_UNIX_SOCKET = '/var/ossim/agent_conn/events_socket'
EVENTS_BSON_UNIX_SOCKET = '/var/ossim/agent_conn/events_bson_socket'
