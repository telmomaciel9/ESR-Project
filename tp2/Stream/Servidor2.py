import sys, socket
import atexit

from random import randint
import sys, traceback, threading, socket

from ServerWorker import TCPWorker, UDPWorker

from VideoStream import VideoStream

class Servidor:

    def __init__(self):
        self.clientInfo = {}
        atexit.register(self.closeConnection)

    def closeConnection(self):
        self.clientInfo["tcpSocket2"].sendall(b"DisconnectStreaming")
        self.clientInfo["tcpSocket2"].close()
        self.clientInfo["tcpSocket"].close()

    def main(self):
        try:
            # Get the media file name
            filename = sys.argv[2]
            print("Using provided video file ->  " + filename)
        except:
            print("[Usage: Servidor.py <videofile>]\n")
            filename = "movie.Mjpeg"
            print("Using default video file ->  " + filename)

        # videoStram
        self.clientInfo['videoStream'] = VideoStream(filename)
        # socket
        self.clientInfo['rtpPort'] = 8888
        self.clientInfo["rtpSocket"] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Create a new socket for RTP/UDP
        self.clientInfo["tcpSocket"] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientInfo["tcpSocket"].bind(("", 9999))
        self.clientInfo["tcpSocket"].listen(5)
        self.clientInfo['event'] = threading.Event()
        self.clientInfo['worker'] = UDPWorker(self.clientInfo['event'], self.clientInfo['videoStream'],
                                              self.clientInfo['rtpPort'], self.clientInfo["rtpSocket"])
        self.clientInfo['worker'].start()
        self.clientInfo["tcpSocket2"] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientInfo["tcpSocket2"].connect((self.clientInfo['Addr'], 8080))
        while True:
            connection, client_address = self.clientInfo["tcpSocket"].accept()
            worker = TCPWorker(self.clientInfo["tcpSocket2"], connection, client_address[0])
            worker.start()

        #cliente/receber
        #addr = '127.0.0.1'
        #port_udp = 5001

        #servidor/enviar
        #port_tcp = 9999
        #server_ip = sys.argv[1]


if __name__ == "__main__":
    (Servidor()).main()