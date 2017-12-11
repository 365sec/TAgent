#Embedded file name: ossim-agent/Conn.py
import os
import re
import socket
import time
import threading
from base64 import b64decode
from struct import unpack
from bson import BSON, InvalidBSON
from bson.binary import STANDARD
from bson.codec_options import CodecOptions
from StringIO import StringIO
from syslog_log import *
from command import *
from TAgentEnums import SessionTypeEnum,SessionTypeStringEnum
lock_uuid = threading.Lock()
CONNECTION_TYPE_SERVER = 1
CONNECTION_TYPE_FRAMEWORK = 2
CONNECTION_TYPE_IDM = 3

class Connection(object):

    def __init__(self, connection_id, connection_ip, connection_port, sensor_id, system_id_file, connection_type, output_queue = None, stats_queue = None, watchdog_queue = None):
        
        self.__stats_queue = stats_queue
        self.__watchdog_queue = watchdog_queue
        self.__is_alive = False
        self.__ip = connection_ip
        self.__id = connection_id
        self.__port = connection_port
        self.__socket_conn = None
        self.__type = connection_type
        self.__sequence = 1
        self.closeLock = threading.RLock()
        self.sendLock = threading.RLock()
        self.connectLock = threading.RLock()
        self.__sensorID = sensor_id
        self.__system_id_file = system_id_file
        self.__patternChangeUUID = re.compile('noack id="(?P<sec>\\d+)" your_sensor_id="(?P<uuid>[a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12})"')
        self.__bson_protocol = True
        
        self.__nameServer = SessionTypeStringEnum.SESSION_TYPE_SERVER
        if self.__type == CONNECTION_TYPE_IDM:
            self.__nameServer = SessionTypeStringEnum.SESSION_TYPE_IDM
        elif self.__type == CONNECTION_TYPE_FRAMEWORK:
            self.__nameServer = SessionTypeStringEnum.SESSION_TYPE_FRAMEWORKD
        self.__sensor_id_change_request_received = False

    @property
    def bson_protocol(self):
        return self.__bson_protocol



    def __set_sensor_id(self, value):
        i = 0
        for ch in value:
            self.__sensorID[i] = ch
            i += 1

    def __get_connection_message(self, bson_protocol):
        if self.__type in [CONNECTION_TYPE_SERVER, CONNECTION_TYPE_IDM]:
            msg = AgentServerConnectionMessage(sequence_id=self.__sequence, sensor_id=str(self.__sensorID[:]))
            if bson_protocol:
                return msg.to_bson()
            else:
                return msg.to_string()
        elif self.__type == CONNECTION_TYPE_FRAMEWORK:
            return AgentFrameworkConnectionMessage(connection_id=self.__id, sensor_id=str(self.__sensorID[:])).to_string()

    def __process_connection_message_bson(self, response):
        message_ok = False
        try:
            bson_msg = BSON.decode(BSON(response), codec_options=CodecOptions(uuid_representation=STANDARD))
            if bson_msg.get('ok') is not None:
                if bson_msg['ok'].get('id', None) == self.__sequence:
                    message_ok = True
            elif bson_msg.get('noack') is not None:
                your_sensor_id = bson_msg['noack'].get('your_sensor_id', None)
                if your_sensor_id is not None:
                    self.__sensor_id_change_request_received = True
                    debug('UUID change request from :%s ' % self.__nameServer)
                    lock_uuid.acquire()
                    self.__write_new_system_id(str(your_sensor_id))
                    self.__set_sensor_id(str(your_sensor_id))
                    lock_uuid.release()
                else:
                    error('Bad response from server')
        except InvalidBSON:
            error('Bad response from server {0}'.format(response))

        return message_ok

    def __process_connection_message_plain(self, response):
        message_ok = False
        if response == 'ok id="' + str(self.__sequence) + '"\n':
            message_ok = True
        else:
            match_data = self.__patternChangeUUID.match(response)
            if match_data:
                dic = match_data.groupdict()
                self.__sensor_id_change_request_received = True
                debug('UUID change request from :%s ' % self.__nameServer)
                lock_uuid.acquire()
                self.__write_new_system_id(dic['uuid'])
                self.__set_sensor_id(dic['uuid'])
                lock_uuid.release()
            else:
                error('Bad response from %s (seq_exp:%s): %s ' % (self.__nameServer, self.__sequence, str(response)))
        return message_ok

    def __process_connection_message_framework(self, response):
        expected_response = 'ok id="' + str(self.__id) + '"\n'
        if response == expected_response:
            return True
        return False

    def __check_connection_message_response(self, response, bson_protocol = False):
        message_ok = False
        if response is None:
            return message_ok
        if self.__type in [CONNECTION_TYPE_SERVER, CONNECTION_TYPE_IDM]:
            if bson_protocol:
                message_ok = self.__process_connection_message_bson(response)
            else:
                message_ok = self.__process_connection_message_plain(response)
        elif self.__type == CONNECTION_TYPE_FRAMEWORK:
            message_ok = self.__process_connection_message_framework(response)
        return message_ok

    def __get_socket(self, blocking = 1, timeout = None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(blocking)
        sock.settimeout(timeout)
        return sock

    def __connect_bson(self):
        connected = False
        self.__socket_conn = self.__get_socket(blocking=1, timeout=60)
        self.__socket_conn.connect((self.__ip, int(self.__port)))
        connection_message = self.__get_connection_message(bson_protocol=True)
        bytes_sent = self.__socket_conn.send(connection_message)
        if bytes_sent != len(connection_message):
            self.close()
            error('Cannot send all the bytes in the message')
        data = self.recv_bson()
        if self.__check_connection_message_response(data, bson_protocol=True):
            info('Connected to %s at  %s:%s!' % (self.__nameServer, self.__ip, self.__port))
            connected = True
            self.__socket_conn.setblocking(1)
            self.__socket_conn.settimeout(None)
        else:
            self.close()
        return connected

    def __connect_plain(self):
        connected = False
        self.__socket_conn = self.__get_socket(blocking=1, timeout=60)
        self.__socket_conn.connect((self.__ip, int(self.__port)))
        connection_message = self.__get_connection_message(bson_protocol=False)
        bytes_sent = self.__socket_conn.send(connection_message)
        if bytes_sent != len(connection_message):
            self.close()
            error('Cannot send all the bytes in the message')
        data = self.recv_line_text()
        if self.__check_connection_message_response(data, bson_protocol=False):
            info('Connected to %s at  %s:%s!' % (self.__nameServer, self.__ip, self.__port))
            connected = True
            self.__socket_conn.setblocking(1)
            self.__socket_conn.settimeout(None)
        else:
            self.close()
        return connected

    def __connect(self):
        if self.__is_alive:
            return
        if self.__type in [CONNECTION_TYPE_SERVER, CONNECTION_TYPE_IDM]:
            while True:
                connected_bson = self.__connect_bson()
                if connected_bson:
                    info('Connected using BSON protocol')
                    self.__is_alive = True
                    return self.__is_alive
                if not self.__sensor_id_change_request_received:
                    break
                self.__sensor_id_change_request_received = False
                info('New sensor id provided, trying connection again')

            warning('Cannot connect using BSON protocol. Trying plain connection.')
            while True:
                connected_plain = self.__connect_plain()
                if connected_plain:
                    info('Connected using PLAIN protocol')
                    self.__is_alive = True
                    return self.__is_alive
                if not self.__sensor_id_change_request_received:
                    break
                self.__sensor_id_change_request_received = False
                info('New sensor id provided, trying connection again')

        elif not self.__connect_plain():
            warning('Cannot connect ')
        else:
            self.__is_alive = True
        return self.__is_alive

    def connect(self, attempts = 3, wait = 10.0):
        self.connectLock.acquire()
        try:
            if self.__socket_conn is None:
                info('Connecting to (%s, %s)..' % (self.__ip, self.__port))
                while attempts > 0:
                    if self.__connect():
                        break
                    error("Can't connect to server ({0}:{1}), retrying in {2} seconds".format(self.__ip, self.__port, wait))
                    time.sleep(wait)
                    attempts -= 1

            else:
                warning('Reusing server connection (%s, %s)..' % (self.__ip, self.__port))
        except Exception as exp:
            error('Cannot connect {0}'.format(str(exp)))
            self.close()
        finally:
            self.connectLock.release()

        return self.__socket_conn


    def __send_stats(self, msg):
        self.__send_message_to_stats(str(msg))

    def __write_new_system_id(self, new_id):
        try:
            with open(self.__system_id_file, 'w') as f:
                f.write(new_id)
            os.chmod(self.__system_id_file, 420)
        except Exception as e:
            error("Can't write sensor file..:%s" % str(e))

    def close(self):
        self.closeLock.acquire()
        try:
            if self.__socket_conn is not None:
                self.__socket_conn.shutdown(socket.SHUT_RDWR)
                self.__socket_conn.close()
        except Exception as exp:
            error('Cannot close the connection cleanly {0}'.format(exp))
        finally:
            self.__socket_conn = None
            self.__is_alive = False
            self.closeLock.release()

    def get_ip(self):
        return self.__ip

    def get_port(self):
        return self.__port

    def get_alive(self):
        return self.__is_alive

    def get_addr(self):
        return self.__socket_conn.getsockname()

    def get_hash(self):
        return self.__ip + ':' + str(self.__port)

    def recv_line_text(self):
        keep_reading = True
        data = ''
        while keep_reading and self.__socket_conn:
            try:
                char = self.__socket_conn.recv(1)
                data += char
                if char == '\n' or char == '' or char is None:
                    keep_reading = False
                if char == '' or char is None:
                    self.close()
            except socket.timeout:
                pass
            except socket.error as e:
                error('Error receiving data from server: ' + str(e))
                keep_reading = False
                self.close()
            except AttributeError as e:
                error('Error receiving data from server - Attribute Error: %s' % str(e))
                keep_reading = False
                self.close()

        return data

    def __recv_bytes(self, bytes_needed, buffer_data = None, read_size = 1):
        if buffer_data is None:
            buffer_data = StringIO()
        bytes_read = 0
        while bytes_read < bytes_needed:
            chunk = self.__socket_conn.recv(read_size)
            chunk_len = len(chunk)
            if chunk_len < 1:
                return
            bytes_read += chunk_len
            buffer_data.write(chunk)

        return buffer_data

    def recv_bson(self):
        try:
            buffer_data = self.__recv_bytes(bytes_needed=4)
            if buffer_data is None:
                return
            message_length, = unpack('<L', buffer_data.getvalue())
            bytes_needed = message_length - 4
            buffer_data = self.__recv_bytes(bytes_needed=bytes_needed, buffer_data=buffer_data)
            bson_object = buffer_data.getvalue()
            buffer_data.close()
        except socket.error as sock_error:
            error('Error receiving data from server - Attribute Error: %s' % str(sock_error))
            self.close()
            bson_object = None

        return bson_object

    def recv_line(self):
        if self.bson_protocol and self.__type in [CONNECTION_TYPE_IDM, CONNECTION_TYPE_SERVER]:
            data = self.recv_bson()
        else:
            data = self.recv_line_text()
        return data

    def send(self, command):
        if self.__is_alive:
            self.sendLock.acquire()
            try:
                if self.bson_protocol and self.__type in [CONNECTION_TYPE_IDM, CONNECTION_TYPE_SERVER]:
                    msg = command.to_bson()
                    self.__socket_conn.send(msg)
                else:
                    self.__socket_conn.send(command.to_string())
            except socket.error as socket_error:
                error('Connection crash: {0}'.format(str(socket_error)))
                self.close()
            except AttributeError as attr_error:
                error('Connection crash: {0}'.format(str(attr_error)))
                self.close()
            except Exception as unknown_exception:
                error('Unexpected exception %s ' % str(unknown_exception))
            else:
                debug(command.to_string().rstrip())
            finally:
                self.sendLock.release()


class ServerConn(Connection):

    def __init__(self, server_ip, server_port, priority, sensor_id,system_id_file, connection_type = CONNECTION_TYPE_SERVER):
        Connection.__init__(self, connection_id='', connection_ip=server_ip, connection_port=server_port, sensor_id=sensor_id, system_id_file=system_id_file, connection_type=connection_type)
        self.__monitor_scheduler = None
        self.__frameworkd_hostname = ''
        self.__frameworkd_ip = ''
        self.__frameworkd_port = ''
        self.__sequence = 0
        self.__priority = priority
        self.__sensor_id = sensor_id
        self.__system_id_file = system_id_file
        self.__thread_control_messages = None
        self.__control_thread_running = False
        self.__stop_event = threading.Event()
        self.__stop_event.clear()

    def control_plugins(self, data):
        pattern = re.compile('(\\S+) plugin_id="([^"]*)"')
        result = pattern.search(data)
        if result is not None:
            command, plugin_id = result.groups()
        else:
            warning('Bad message from server: %s' % data)
            return
        """
        if command == WatchDogData.PLUGIN_START_REQ:
            self.watchdog_start_process(int(plugin_id))
        elif command == WatchDogData.PLUGIN_STOP_REQ:
            self.watchdog_stop_process(int(plugin_id))
        elif command == WatchDogData.PLUGIN_ENABLE_REQ:
            self.watchdog_enable_process(int(plugin_id))
        elif command == WatchDogData.PLUGIN_DISABLE_REQ:
            self.watchdog_disable_process(int(plugin_id))
        """

    def control_monitors(self, data):
        """
        watch_rule = WatchRule()
        for attr in watch_rule.EVENT_ATTRS:
            pattern = ' %s="([^"]*)"' % attr
            result = re.findall(pattern, data)
            if result:
                value = result[0]
                if attr in watch_rule.EVENT_BASE64:
                    value = b64decode(value)
                watch_rule[attr] = value

        for plugin in self.plugins:
            if plugin.get('config', 'plugin_id') == watch_rule['plugin_id'] and plugin.get('config', 'type').lower() == 'monitor':
                self.__monitor_scheduler.new_monitor(monitor_type=plugin.get('config', 'source'), plugin=plugin, watch_rule=watch_rule)
                break
        """
        pass

    def __process_plain_control_message(self, data):
        info('Received message from server: ' + data.rstrip())

        if data.startswith('watch-rule'):
            self.control_monitors(data)
        elif data.startswith('ping'):
            self.send(AgentServerCommandPong())

    def __process_bson_control_message(self, data):
        data_json = BSON.decode(BSON(data), codec_options=CodecOptions(uuid_representation=STANDARD))
        if data_json.get('ping', None):
            t = data_json.get('ping').get('timestamp')
            info('Ping request with timestamp %d' % t)
            self.send(AgentServerCommandPong())
        elif data_json.get('watch-rule', None):
            self.control_monitors(data_json.get('watch-rule').get('str', ''))
        elif data_json.get('sensor-plugin-start', None):
            plugin_id = data_json.get('sensor-plugin-start').get('plugin_id', None)
            if plugin_id is not None:
                self.watchdog_start_process(int(plugin_id))
        elif data_json.get('sensor-plugin-stop', None):
            plugin_id = data_json.get('sensor-plugin-stop').get('plugin_id', None)
            if plugin_id is not None:
                self.watchdog_stop_process(int(plugin_id))
        elif data_json.get('sensor-plugin-enable'):
            plugin_id = data_json.get('sensor-plugin-enable').get('plugin_id', None)
            if plugin_id is not None:
                self.watchdog_enable_process(int(plugin_id))
        elif data_json.get('sensor-plugin-disable'):
            plugin_id = data_json.get('sensor-plugin-disable').get('plugin_id', None)
            if plugin_id is not None:
                self.watchdog_disable_process(int(plugin_id))
        else:
            warning("Unknown BSON command: '%s'" % str(data_json))

    def recv_control_messages(self, event):
        while not event.is_set():
            try:
                data = self.recv_line()
                if data is not None:
                    if self.bson_protocol:
                        self.__process_bson_control_message(data)
                    else:
                        self.__process_plain_control_message(data)
                else:
                    self.close()
            except socket.error:
                self.close()
            except Exception as e:
                if not event.is_set():
                    error('Unexpected exception receiving from AlienVault server: ' + str(e))

            time.sleep(0.01)

        info('Ends control message thread..')

    def append_plugins(self):
        """
        for plugin in self.plugins:
            state = 'start' if plugin.getboolean('config', 'enable') else 'stop'
            message = AppendPlugin(plugin_id=int(plugin.get('config', 'plugin_id')), sequence_id=int(self.__sequence), state=state, enabled=plugin.getboolean('config', 'enable'))
            self.send(message)
        """
        pass

    def control_messages(self):
        """
        if self.__control_thread_running:
            info('control message not started. .... already started')
            return
        if self.__monitor_scheduler is None:
            self.__monitor_scheduler = MonitorScheduler(output_queue=self.__output_queue, stop_event=self.__stop_event)
        self.__monitor_scheduler.start()
        self.__stop_event.clear()
        self.__control_thread_running = True
        self.__thread_control_messages = threading.Thread(target=self.recv_control_messages, args=(self.__stop_event,))
        self.__thread_control_messages.start()
        """
        pass

    def get_framework_data(self):
        return (self.__frameworkd_hostname, self.__frameworkd_ip, self.__frameworkd_port)

    def get_priority(self):
        return self.__priority

    def set_framework_data(self, hostname, ip, port):
        self.__frameworkd_hostname = hostname
        self.__frameworkd_ip = ip
        self.__frameworkd_port = port

    def close(self):
        try:
            self.__stop_event.set()
            self.__monitor_scheduler = None
            self.__control_thread_running = False
            self.__thread_control_messages = None
            super(ServerConn, self).close()
        except Exception:
            info('AlienVault Server connection closed...')


class IDMConn(Connection):

    def __init__(self, idm_ip, idm_port, sensor_id, system_id_file, connection_type = CONNECTION_TYPE_IDM):
        Connection.__init__(self, '', idm_ip, idm_port, sensor_id, system_id_file, connection_type)
        self.__idm_ip = idm_ip
        self.__idm_port = idm_port
        self.__conn = None
        self.__control_thread_running = False
        self.__control_thread = None
        self.__stopEvent = threading.Event()
        self.__stopEvent.clear()

    def start_control(self):
        self.__stopEvent.clear()
        self.__start_control_messages()

    @property
    def control_thread_running(self):
        return self.__control_thread_running

    @control_thread_running.setter
    def control_thread_running(self, value):
        self.__control_thread_running = value

    @property
    def ip(self):
        return self.__idm_ip

    @property
    def port(self):
        return self.__idm_port

    def control_loop(self, stop_event):
        while not stop_event.is_set():
            try:
                data = self.recv_line()
                if data is not None:
                    if self.bson_protocol:
                        data_json = BSON.decode(BSON(data), codec_options=CodecOptions(uuid_representation=STANDARD))
                        if data_json.get('ping', None):
                            t = data_json.get('ping').get('timestamp')
                            self.send(AgentServerCommandPong(timestamp=long(t)))
                    elif data.startswith('ping'):
                        self.send(AgentServerCommandPong())
                else:
                    self.close()
            except Exception as e:
                if not stop_event.is_set():
                    import traceback
                    error('Unexpected exception receiving from IDM server: {0}' + str(e))

            time.sleep(1)

        info('Ends IDM control message thread..')
        self.control_thread_running = False

    def __start_control_messages(self):
        self.__control_thread_running = True
        self.__control_thread = None
        self.__control_thread = threading.Thread(target=self.control_loop, args=(self.__stopEvent,))
        self.__control_thread.start()

    def close(self):
        self.__control_thread = None
        info('Closing AlienVault IDM connection ...')
        self.__stopEvent.set()
        super(IDMConn, self).close()


class FrameworkConn(Connection):

    def __init__(self, conf, frmk_id, frmk_ip, frmk_port, sensor_id, system_id_file):
        Connection.__init__(self, frmk_id, frmk_ip, frmk_port, sensor_id, system_id_file, CONNECTION_TYPE_FRAMEWORK)
        self._framework_id = frmk_id
        self._framework_ip = frmk_ip
        self._framework_port = frmk_port
        self._framework_ping = True
        self.__control_manager = None
        self.__pingThread = None
        self.__conf = conf
        self.__sensorID = sensor_id
        self.__control_messages_listener = None
        self.__stopEvent = threading.Event()
        self.__stopEvent.clear()

    def close(self):
        info('Closing control framework connection ...')
        self.__stopEvent.set()
        super(FrameworkConn, self).close()

    def __recv_frmk_control_messages(self, e):
        while not e.isSet():
            try:
                data = self.recv_line().rstrip('\n')
                if data == '':
                    continue
                response = self.__control_manager.process(self.get_addr(), data)
                while len(response) > 0:
                    self.send(AgentFrameworkCommand(response.pop(0)))

                time.sleep(1)
            except Exception as exp:
                error('Framework Connection: %s' % str(exp))

        self.__control_manager.stopProcess()
        info('Closing thread - receive control framework control messages...!')

    def __ping(self, e):
        while not e.isSet():
            self.send(AgentFrameworkCommandPong())
            time.sleep(30)

    def frmk_control_messages(self):
        self.__stopEvent.clear()
        """
        self.__control_manager = ControlManager(self.__conf, self.__sensorID)
        self.__control_messages_listener = threading.Thread(target=self.__recv_frmk_control_messages, args=(self.__stopEvent,))
        self.__control_messages_listener.start()
        if self._framework_ping:
            self.__pingThread = threading.Thread(target=self.__ping, args=(self.__stopEvent,))
            self.__pingThread.start()
        """


if __name__ == '__main__':
   server_ip = "172.16.39.99"
   server_port = 80 
   priority = 1
   sensor_id= "99-999"
   system_id_file = ""
   server = ServerConn( server_ip, server_port, priority, sensor_id,system_id_file)
   server.connect()
