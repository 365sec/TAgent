import select
import socket
from struct import unpack
from Config import CommandLineOptions
from Conn import ServerConn,get_uuid
from jinja2.ext import do
import Queue
from worker import Worker
from sender import Sender
from heartbeat import Heartbeat
from Config import  Conf
import os
from __builtin__ import True

class Agent():

    def __init__(self):
        self.options = CommandLineOptions().get_options()
        self.server_connection  = None
        self.send_packet_queue = Queue.Queue(maxsize=0)
        self.recv_packet_queue = Queue.Queue(maxsize=0)
        self.config = Conf()
        self.config.read([os.path.join(os.path.dirname(os.path.realpath(__file__)),"config.cfg")])

    
    def working(self):
        print "am working "
        
    def get_bson_packet(self,buffer_data,len):
        if len <4 :
          return None,buffer_data
        message_length, = unpack('<L', buffer_data[0:4])
        if len < message_length:
            return None,buffer_data
        
        return buffer_data[0:message_length],buffer_data[message_length:len]
    
    def __start_agent(self):
       server_ip = self.config.get("server","ip")
       server_port = int(self.config.get("server","port"))
       sensor_id= self.config.get("agent","id")
       
       priority = 1
       system_id_file = ""   
 
       Worker(self.recv_packet_queue,self.send_packet_queue).start()
      
       self.server_connection = ServerConn( server_ip, server_port, priority, sensor_id,system_id_file)
       server_socket = self.server_connection.connect()
       if server_socket == None :
           print "connect failed !"
           exit(0);
           
       Sender(self.send_packet_queue,self.server_connection).start()
       Heartbeat(self.send_packet_queue).start()
       
       server_socket.setblocking(False)
       read_buff = ""
       print "===="
       while True:
          readable, writable, exceptional = select.select([self.server_connection.get_connectsocket()], [], [self.server_connection.get_connectsocket()])
          #handle read event
          try:
              if server_socket in readable :
                  #construct packet
                  chunk= server_socket.recv(1024*1024)
                  read_buff += chunk
                  read_buff_len = len(read_buff)
                  print read_buff_len
                  while( read_buff_len > 4) :
                     packet, read_buff = self.get_bson_packet(read_buff,read_buff_len)
                     if packet:
                       print "push a packet"
                       self.recv_packet_queue.put(packet)
                       read_buff_len = len(read_buff)
                     else :
                       break
                     
          except  Exception as e:
               print e
                 
                 
          for s in exceptional:
              print "socket --has exceptional"
       
       
    def start(self):
       self.__start_agent()
        


if __name__ == "__main__":
    agent = Agent()
    agent.start()
