# main_server.py
import sys
import threading
from TCPServer import TCPServer
from UDPServer import UDPServer
from bootstrap import Bootstrap

def parserArgs(arg):
    ip, porta = sys.argv[arg].split(":")
    return ip, int(porta)

class MainServer():
    def __init__(self, bootstrap_mode):
        self.wg = threading.Event()
        self.threads = []
        self.mode=bootstrap_mode
        if self.mode:
            self.bootstrap= Bootstrap()
        self.tcp_server = TCPServer("10.0.0.10", "3000",self.mode)
        self.udp_server = UDPServer()
        

    def start(self):
        
        self.threads.append(threading.Thread(target=self.tcp_server.start))
        self.threads.append(threading.Thread(target=self.udp_server.start))
        if self.mode:
            self.threads.append(threading.Thread(target=self.bootstrap.start))

        for thread in self.threads:
            thread.start()

    def stop(self):
        self.wg.set()
        for thread in self.threads:
            thread.join()
        self.tcp_server.stop()
        self.udp_server.stop()

if __name__ == "__main__":
    # in case bootstrap mode is 1, otherwise, it is equal to 0
    bootstrap_mode = 0
    bootstrap_ip = bootstrap_port = None  # Initialize to None

    if len(sys.argv)>1 and sys.argv[1] == "--b":
        bootstrap_mode = 1
        #bootstrap_ip, bootstrap_port = parserArgs(2)



    main_server = MainServer(bootstrap_mode)
    main_server.start()