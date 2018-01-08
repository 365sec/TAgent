import threading
import select
import socket

class Sender(threading.Thread):
    def __init__(self,send_queue,server_socket):
        threading.Thread.__init__(self)
        self.send_queue = send_queue
        self.server_socket = server_socket

        
    def send_packet(self,packet):
        length = len(packet)
        bytes_sent = 0
        try: 
            while length-bytes_sent > 0:
               readable, writable, exceptional = select.select([], [self.server_socket], [])
               
               if self.server_socket  in writable:
                 n = self.server_socket.send(packet[bytes_sent:])
                 print "send--",n
                 bytes_sent = bytes_sent+n
               
        except socket.error as socket_error:
            print('Connection crash: {0}'.format(str(socket_error)))
        except Exception as e :
            print e
             
           
           
    def run(self):
        print "thread sender starting"
        while True:
           packet = self.send_queue.get()
           self.send_packet(packet)
           