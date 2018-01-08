import threading

from bson import BSON, InvalidBSON
from bson.binary import STANDARD
from bson.codec_options import CodecOptions
from command import *
from syslog_log import *

class Worker(threading.Thread):
    def __init__(self,recv_queue,send_queue):
        threading.Thread.__init__(self)
        print "__thread init"
        self.recv_queue = recv_queue
        self.send_queue = send_queue
        
    
    def __process_bson_control_message(self, data):
        data_json = BSON.decode(BSON(data), codec_options=CodecOptions(uuid_representation=STANDARD))
        print data_json
        if data_json.get('exc_cmd', None):
            t = data_json.get('exc_cmd').get('cmdline')
            info('exc_cmd request with timestamp %s' % t)
            self.send_queue.put(AgentServerCommandExc().to_bson())

        else:
            warning("Unknown BSON command: '%s'" % str(data_json))
    
    
    def run(self):
        print "Workering ..."
        while True:
           packet = self.recv_queue.get()
           self.__process_bson_control_message(packet)
        
