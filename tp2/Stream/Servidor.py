import atexit
import socket
import sys
import threading
import traceback
import re
from RtpPacket import RtpPacket
from VideoStream import VideoStream


class UDPWorker(threading.Thread):
    def __init__(self, event, videoStream, rtpPort, rtpSocket, RPAddr):
        threading.Thread.__init__(self)
        self.event = event
        self.videoStream = videoStream
        self.rtpPort = rtpPort
        self.rtpSocket = rtpSocket
        self.RPaddress = RPAddr

    def run(self):
        """Send RTP packets over UDP."""
        while True:
            self.event.wait(0.05)

            # Stop sending if request is PAUSE or TEARDOWN
            if self.event.isSet():
                break

            data = self.videoStream.nextFrame()
            if data:
                frameNumber = self.videoStream.frameNbr()
                try:
                    ##address = socket.gethostbyname("127.0.0.1")
                    port = int(self.rtpPort)
                    packet = self.makeRtp(data, frameNumber)
                    self.rtpSocket.sendto(packet, (self.RPaddress, port))
                except:
                    print("Connection Error")
                    print('-' * 60)
                    traceback.print_exc(file=sys.stdout)
                    print('-' * 60)
        # Close the RTP socket
        self.rtpSocket.close()
        print("All done!")

    def makeRtp(self, payload, frameNbr):
        """RTP-packetize the video data."""
        version = 2
        padding = 0
        extension = 0
        cc = 0
        marker = 0
        pt = 26  # MJPEG type
        seqnum = frameNbr
        ssrc = 0

        rtpPacket = RtpPacket()

        rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)
        #print("Encoding RTP Packet: " + str(seqnum))

        return rtpPacket.getPacket()


class TCPWorker(threading.Thread):
    def __init__(self, tcpSocket, RPconnection_socket, RPAddr):
        threading.Thread.__init__(self)
        self.RPconnection_socket = RPconnection_socket
        self.RP_ip = RPAddr
        self.tcpSocket = tcpSocket

    def run(self):
        while True:
            received = self.RPconnection_socket.recv(1024).decode()
            print(f"\nRecebi isto: {received}")
            if received == "Stream":
                print("Ola")
                self.tcpSocket.send(("Stream|" + self.RP_ip).encode())
                print(self.tcpSocket.getpeername()[0])
                print(self.tcpSocket.getsockname()[0])
                print("slslslsl")
            else:
                print("Adeus") 
                self.tcpSocket.send(("Stop|" + self.RP_ip).encode())
                print("ehehehe")
                break

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
            # Get the rp IP address
            self.clientInfo['Addr'] = sys.argv[1]
            print("RP address ->  " + self.clientInfo['Addr'])
            # Get the media file name
            filename = sys.argv[2]
            print("Using provided video file ->  " + filename)
        except:
            print("[Usage: Servidor.py <rp_ip> <videofile>]\n")
            filename = "movie.Mjpeg"
            print("Using default video file ->  " + filename)

        # videoStram
        self.clientInfo['videoStream'] = VideoStream(filename)
        # socket
        self.clientInfo['rtpPort'] = 3000

        # Create a new socket for RTP/UDP
        self.clientInfo["rtpSocket"] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


        self.clientInfo["tcpSocket"] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientInfo["tcpSocket"].bind(("", 4000))
        self.clientInfo["tcpSocket"].listen(0)


        self.clientInfo['event'] = threading.Event()
        self.clientInfo['worker'] = UDPWorker(self.clientInfo['event'], self.clientInfo['videoStream'],
                                              self.clientInfo['rtpPort'], self.clientInfo["rtpSocket"],self.clientInfo['Addr'])
        self.clientInfo['worker'].start()


        self.clientInfo["tcpSocket2"] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientInfo["tcpSocket2"].connect((self.clientInfo['Addr'], 4000))
        self.clientInfo["tcpSocket2"].send("Server connected".encode())
        print(self.clientInfo["tcpSocket2"].getpeername())
        print(self.clientInfo["tcpSocket2"].getsockname())
        while True:
            RPconnection_socket, RP_address = self.clientInfo["tcpSocket"].accept()
            worker = TCPWorker(self.clientInfo["tcpSocket2"], RPconnection_socket, RP_address[0])
            worker.start()


if __name__ == "__main__":
    (Servidor()).main()