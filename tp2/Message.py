class Message:
    def __init__(self,id,src,dest,data):
        self.id = id
        self.src = src
        self.dest = dest
        self.data = data

    def getId(self):
        return self.id
    
    def getSrc(self):
        return self.src

    def getDest(self):
        return self.dest

    def getData(self):
        return self.data

    def setId(self,id):
        self.id = id
    
    def setSrc(self,src):
        self.src = src

    def setDest(self,dest):
        self.dest = dest

    def setData(self,data):
        self.data = data

    def pprint(self):
        return f"\nMESSAGE : {self.id}\n\tFrom : {self.src}\n\tTO: {self.dest}\n\tData : {self.data}\n"

'''
1 - cliente pede ao bootstrap os seus viz
2 - bootstrap indica que o nodo é viz e envia os viz com sucesso
3 - bootstrap indica que o nodo não é data topologia
4 - Cliente diz ao bootstrap que já recebeu e fecha comunicação com o bootstap

5 - Um Nodo diz um ola ao vizinho do lado
6 - Diz ola de volta 
7 - Confirmar que consegue receber comunicações com o vizinho

8 - um nodo a pedir a stream (na parte de informação adicionar recursivamente o caminho que vai fazendo 
                                - para depois no rp conseguir implementar na arvore
                                - no campo da mensagem indicar o timestamp) 
9 - a enviar a stream (indicar a diferença)




'''