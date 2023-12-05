import sys
from tkinter import Tk
from ClienteGUI import ClienteGUI
import re

if __name__ == "__main__":
        addr = '127.0.0.1'
        port_udp = 3000
        port_tcp = 4000
        node_ip = sys.argv[1]

        root = Tk()

        # Create a new client
        app = ClienteGUI(root, addr, port_udp, node_ip, port_tcp)
        app.master.title("Cliente Exemplo")
        root.mainloop()