import sys
from tkinter import Tk
from ClienteGUI import ClienteGUI
	
if __name__ == "__main__":
    try:
        addr = '127.0.0.1'
        port_udp = 5000
        port_tcp = 4000
        server_ip = sys.argv[1]

        root = Tk()

        # Create a new client
        app = ClienteGUI(root, addr, port_udp, server_ip, port_tcp)
        app.master.title("Cliente Exemplo")
        root.mainloop()
    except IndexError:
        print("[Usage: Cliente.py]")
		
	
