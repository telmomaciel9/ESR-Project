import atexit
import socket
import sys
import threading
import traceback
import queue
import time
import json
import re
from RtpPacket import RtpPacket
from VideoStream import VideoStream
from Message import Message


class serverThread(threading.Thread):
    def __init__(self, ip_rp, videoName):
        threading.Thread.__init__(self)
        self.ip_rp = ip_rp
        self.video = VideoStream(videoName)

    def stop(self):
        self._stop_event.set()

    def makeRtp(self, data, fn):
        rtpPacket = RtpPacket()
        rtpPacket.encode(2, 0, 0, 0, fn, 0, 26, 0, data)
        return rtpPacket.getPacket()

    def run(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        while True:  # Check _stop_event in the loop
            print("\nA Streamar!")
            time.sleep(0.05)
            data = self.video.nextFrame()
            if data:
                frameNumber = self.video.frameNbr()
                packet = self.makeRtp(data, frameNumber)
                udp_socket.sendto(packet, (self.ip_rp, 3000))
            else:
                self.video.seek()


class Server:	
    def __init__(self,rp_ip):
        self.rp_ip = rp_ip

        self.wg = threading.Event()
        self.lock = threading.Lock()

        self.receive_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.receive_socket.bind(('',4000))
        self.receive_socket.listen(5)

        self.send_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.is_Streaming = False
        self.receive_queue = queue.Queue()
        self.process_queue = queue.Queue()


    def receive_messages(self):
        while True:
            try:
                client_socket, client_address = self.receive_socket.accept()
                print(f"\nServer [RECEIVE THREAD] : CONNECTED WITH {client_address}")
                data = client_socket.recv(1024)
                client_address = client_socket.getpeername()[0]
                host_addr = client_socket.getsockname()[0]
                print(f"\nServer [RECEIVE THREAD] : RECEIVED THIS MESSAGE FROM {client_address}: {data}")
                if not data:
                    break
                with self.lock:
                    try:
                        # Try to decode the data as JSON
                        json_data = json.loads(data.decode())
                        is_json = True
                    except json.JSONDecodeError:
                        # If decoding fails, assume it's not JSON
                        is_json = False

                    if is_json:
                        self.receive_queue.put((data, host_addr, client_address, True))
                    else:
                        self.receive_queue.put((data, host_addr, client_address, False))

            except Exception as e:
                print(f"\nServer : An error occurred while receiving messages: {e}")


    def process_messages(self):
            while True:
                with self.lock:
                    if not self.receive_queue.empty():
                        data,host_addr,client_address,isMessage = self.receive_queue.get()
                        print(f"\nRP [PROCESS TREAD] : GOING TO PROCESS A MESSAGE {data}")
                        try:
                            message_data = None

                            if isMessage:
                            # Deserialize the JSON data into a Python object
                                message_data = json.loads(data.decode())
                            else:
                                message_data = data.decode()

                            if message_data["id"] == "14" and not self.is_Streaming:
                                self.is_Streaming = True
                                print("vou começar a streamar!\n")
                                serverStreamer = serverThread(self.rp_ip,"movie.Mjpeg")
                                print("ejejej")
                                serverStreamer.start()
                                print("eheheh")
                            
                            elif message_data["id"] == "15" and self.is_Streaming:
                                self.is_Streaming = False
                                serverStreamer.stop()


                        except json.JSONDecodeError as e:
                            print(f"\nServer [PROCESS TREAD] : Error decoding JSON data: {e}")
                        except Exception as e:
                            print(f"\nServer [PROCESS TREAD] : Error in processing messages: {e}")

    #Função para enviar as mensagens que estão na queue de mensagens já processadas
    def send_messages(self):
        while True:
            with self.lock:
                if not self.process_queue.empty():
                    client_socket = None
                    print(f"\n\Size da queue : {self.process_queue.qsize()}")
                    data, client_socket, Socket_is_Created = self.process_queue.get()
                    ip_destino = ""
                    port_destino = 4000
                    try:
                        # Try to decode the data as JSON
                        message_data = json.loads(data)
                        ip_destino = message_data["dest"][0]
                        port_destino = message_data["dest"][1]
                    except json.JSONDecodeError:
                        # If decoding fails, assume it's not JSON
                        ip_destino = client_socket.getpeername()[0]
                        print(ip_destino)
                    if not Socket_is_Created:
                        client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                        client_socket.connect((ip_destino,port_destino))
                        #self.clients_sockets.append(client_socket)
                    try:
                        client_socket.send(data.encode())
                        print(f"\nRP [SEND THREAD] : SENT THIS MESSAGE TO ({ip_destino},{port_destino}) : {data} ")
                    except json.JSONDecodeError as e:
                        print(f"\nRP [SEND THREAD] : Error decoding JSON data: {e}")
                    except Exception as e:
                        print(f"\nRP [SEND THREAD] :  Error sending message in the send_messages function: {e}")

    def connect_to_other_node(self, ip, port, purpose):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        attempt_count = 0
        #while attempt_count < 3:  # Adjust the maximum number of attempts as needed
        #time.sleep(5)
        try:
            client_socket.connect((ip, port))
            if purpose == 1:
                messagem = Message("13",client_socket.getsockname()[0],(ip,port),client_socket.getsockname()[0])
                self.process_queue.put((json.dumps(messagem.__dict__),client_socket,True))
           
        except Exception as e:
            print(f"\nRP: An error occurred while sending a message in connect_to_other_node function in ip {ip}: {e}")
            attempt_count += 1
            print(f"\nRP : Retrying connection to {ip}:{port}... (Attempt {attempt_count})")
            time.sleep(2)  # Adjust the delay between attempts as needed
        #if attempt_count >= 3:
        #    print(f"\nFailed to establish a connection to {ip}:{port} after multiple attempts.")

    def start(self):
        try:
            while not self.wg.is_set():
                receive_thread = threading.Thread(target=self.receive_messages, args=())
                process_thread = threading.Thread(target=self.process_messages, args=())
                send_thread = threading.Thread(target=self.send_messages, args=())
                receive_thread.start()
                process_thread.start()
                send_thread.start()

                self.connect_to_other_node(self.rp_ip,4000,1)
    
                receive_thread.join()
                process_thread.join()
                send_thread.join()
        except Exception as e:
            print(f"\RP : An error occurred in start function: {e}")
        finally:
            #for client_socket in self.clients:
            #    client_socket.close()
            if self.receive_socket:
                self.receive_socket.close()
            if self.send_socket:
                self.send_socket.close()

if __name__ == "__main__":
    rp_ip = sys.argv[1]
    servidor = Server(rp_ip)
    servidor.start()




