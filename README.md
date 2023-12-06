# ESR

## Parte da comunicação - TCP

Bootstrap (ser sempre o primeiro a correr):

    python3 ONode.py --b


Nodo intermédio:

    python3 ONode.py <bootstrap_ip>


RP:
    
    python3 ONode.py --rp <bootstrap_ip>


Cliente (teste para o flood):

    python3 TCPSender.py <ip_nodo_mais_prox>

## Parte de envio de Streaming - UDP

Cliente:

    export DISPLAY=:0.0

    python3 Cliente.py <server_ip> <server_port> <self_port> <movieName>

Servidor:

    python3 Servidor.py <self_port>




---
### Portas

- porta para o TCP: 4000

- porta para o UDP: 3000