import socket
import sys
import threading
import traceback

from RtpPacket import RtpPacket

class UDPWorker(threading.Thread):
    def __init__(self, event, videoStream, rtpPort, rtpSocket):
        threading.Thread.__init__(self)
        self.event = event
        self.videoStream = videoStream
        self.rtpPort = rtpPort
        self.rtpSocket = rtpSocket

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
                    address = socket.gethostbyname("127.0.0.1")
                    port = int(self.rtpPort)
                    packet = self.makeRtp(data, frameNumber)
                    self.rtpSocket.sendto(packet, (address, port))
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
    def __init__(self, tcpSocket:socket.socket, connection, clientAddr):
        threading.Thread.__init__(self)
        self.connection = connection
        self.client_ip = clientAddr
        self.tcpSocket = tcpSocket

    def run(self):
        while True:
            received = self.connection.recv(1024).decode("UTF-8")
            if received == "Stream":
                self.tcpSocket.sendall((bytes("Stream|" + self.client_ip,"utf-8")))
            else:
                self.tcpSocket.sendall((bytes("Stop|" + self.client_ip,"utf-8")))