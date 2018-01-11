import threading

from bson import BSON, InvalidBSON
from bson.binary import STANDARD
from bson.codec_options import CodecOptions
from command import *
from syslog_log import *
import os

class Worker(threading.Thread):
    def __init__(self,recv_queue,send_queue):
        threading.Thread.__init__(self)
        print "__thread init"
        self.recv_queue = recv_queue
        self.send_queue = send_queue
        
    
    def __process_exc_cmd(self,data_json):
        try:
            header= data_json.get('header')
            cmdline = data_json.get('exc_cmd').get('cmdline')
            
            output = os.popen(cmdline) 
            self.send_queue.put(AgentServerCommandExc(header,"".join(output.readlines())).to_bson())
        except Exception as err:
            print err
            
    def __process_file_upload(self,data_json):
        try :
            header= data_json.get('header')
            filename = data_json.get('fileupload').get('filename')
            content = data_json.get('fileupload').get('content')
            fp = open(os.path.join(os.path.dirname(os.path.realpath(__file__)),"upload",filename),"wb")
            fp.write(content)
            fp.close()
         
            self.send_queue.put(AgentServerCommandFileUpload(header,"GOOD I RECV A FILE").to_bson())
        except Exception  as e:
            print e
        
            
    def __process_bson_control_message(self, data):
        data_json = BSON.decode(BSON(data), codec_options=CodecOptions(uuid_representation=STANDARD))
        #print data_json
        if data_json.get('exc_cmd', None):
            self.__process_exc_cmd(data_json)
        elif data_json.get('fileupload', None):
            self.__process_file_upload(data_json)
        else:
            warning("Unknown BSON command: '%s'" % str(data_json))
    
    
    def run(self):
        print "Worker"
        while True:
           packet = self.recv_queue.get()
           self.__process_bson_control_message(packet)
        
        
if __name__ == "__main__":
    output = os.popen('ifconfig')
    
   
    print "".join(output.readlines())