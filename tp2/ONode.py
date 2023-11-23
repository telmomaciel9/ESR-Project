# main_server.py
import sys
import threading
from ONodeTCP import ONodeTCP
from ONodeUDP import ONodeUDP
from bootstrap import Bootstrap
from RP import RP


class ONode():
    def __init__(self, bootstrap_ip,bootstrap_mode):
        self.wg = threading.Event()
        self.threads = []
        self.mode=bootstrap_mode    
        if self.mode:
            self.bootstrap= Bootstrap()
        self.ONode_tcp = ONodeTCP(bootstrap_ip,self.mode)
        self.ONode_udp = ONodeUDP()
        

    def start(self):
        
        self.threads.append(threading.Thread(target=self.ONode_tcp.start))
        self.threads.append(threading.Thread(target=self.ONode_udp.start))
        if self.mode:
            self.threads.append(threading.Thread(target=self.bootstrap.start))

        for thread in self.threads:
            thread.start()

    def stop(self):
        self.wg.set()
        for thread in self.threads:
            thread.join()
        self.ONode_tcp.stop()
        self.ONode_udp.stop()

if __name__ == "__main__":
    # in case bootstrap mode is 1, otherwise, it is equal to 0
    bootstrap_mode = 0
    rp_mode = 0
    bootstrap_ip = "" # Initialize to None

    if (len(sys.argv) <3):
        if(sys.argv[1].lower() == "--b"):
            bootstrap_mode = 1
        elif(sys.argv[1].lower() == "--rp"):    
            rp_mode = 1
            #abordagem para saber os servidores era passar como um argumento
        else:
            bootstrap_ip = sys.argv[1]
    if(len(sys.argv)>2 and len(sys.argv)<4):
        if((sys.argv[1].lower() == "--rp" and sys.argv[2].lower() == "--b") or (sys.argv[2].lower() == "--rp" and sys.argv[1].lower() == "--b")):
            bootstrap_mode=1
            rp_mode = 1


    ONode = ONode(bootstrap_ip,bootstrap_mode)
    ONode.start()