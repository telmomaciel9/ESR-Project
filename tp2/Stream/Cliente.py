import sys
from tkinter import Tk
from ClienteGUI import ClienteGUI
	
if __name__ == "__main__":
    try:
        addr = '127.0.0.1'
        port = 25000
        server_port = 9999
        server_ip = sys.argv[1]

        root = Tk()

        # Create a new client
        app = ClienteGUI(root, addr, port, server_ip, server_port)
        app.master.title("Cliente Exemplo")
        root.mainloop()
    except IndexError:
        print("[Usage: Cliente.py]")
		
	
