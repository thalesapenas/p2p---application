import threading
from socket import *
import random
import string
import pickle
import os
import queue

class objectPeer:
    def __init__(self, server_address,server_port, card):
        self.serverPort = server_port 
        self.serverAddress = server_address
        self.card = card

class Peer:
    def __init__(self, server_port):
        self.serverPort = server_port
        self.serverSocket = socket(AF_INET, SOCK_STREAM)
        self.serverSocket.bind(("", self.serverPort))
        self.serverSocket.listen(5)  # Permitindo até 5 conexões em espera
        self.server_address = self.serverSocket.getsockname()
        
        self.net_ip = None
        self.net_port = None
        
        self.list_of_peers = []
        self.card = self.load_card() or self.generate_random_card()
        self.save_card()
        self.trade_requests = queue.Queue()
        self.trade_search_results = queue.Queue()
        
        self.listen_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
        self.listen_thread.start()

    def generate_random_card(self):
        return random.choice(string.ascii_uppercase)

    def save_card(self):
        with open(f'peer_{self.serverPort}_card.pkl', 'wb') as f:
            pickle.dump(self.card, f)

    def load_card(self):
        try:
            if os.path.exists(f'peer_{self.serverPort}_card.pkl'):
                with open(f'peer_{self.serverPort}_card.pkl', 'rb') as f:
                    return pickle.load(f)

        except Exception as e:
            return e
            
    def listen_for_messages(self):
        while True:
            connectionSocket, addr = self.serverSocket.accept()
            print(f"Connection from {addr}")
            threading.Thread(target=self.handle_message, args=(connectionSocket,), daemon=True).start()

    def handle_message(self, connectionSocket):
        flag = 0
        while True:
            try:
                sentence = connectionSocket.recv(1024).decode()
                if not sentence:
                    continue

                print("\nReceived message:", sentence)

                if sentence.startswith("TRADE_REQUEST"):
                    _, sender_ip, sender_port, proposed_card = sentence.split(',')
                    self.trade_requests.put((sender_ip, sender_port, proposed_card))
                    
                elif sentence.startswith("LIST_PEERS_FROM:"):
                    parts = sentence.split(":", 3)
                    server_address = parts[1]
                    server_port = parts[2]
                    peer_data = parts[3]
                    
                    # Salve as informações do servidor no cliente
                    self.net_ip = server_address
                    self.net_port = server_port
                    
    
                    self.list_of_peers.clear()
                    peer_list = peer_data.split(',')
                    self.list_of_peers = [objectPeer(*peer.split(':')) for peer in peer_list]
                    
                    print(f"Received peer list from {server_address}:{server_port}")

                elif sentence.startswith("FILE_TRANSFER"):
                    self.receive_file('peer_{}_card.pkl'.format(self.serverPort), connectionSocket)
                    
                    
                elif sentence.startswith("TRADE_CONFIRM"):
                    _, sender_ip, sender_port, new_card = sentence.split(',')
                    print(f"Trade confirmed with {sender_ip}:{sender_port}. New card: {new_card}")
                    old_card = self.card
                    self.card = new_card
                    traded_peer = objectPeer(sender_ip, sender_port, old_card)
                    for p in self.list_of_peers:
                        if p.serverAddress == sender_ip and p.serverPort == sender_port:
                            self.list_of_peers.remove(p)
                            break
                    self.list_of_peers.append(traded_peer)

                    self.send_file_and_message(f'peer_{self.serverPort}_card.pkl', "FILE_TRANSFER", sender_ip, int(sender_port))
                    self.receive_file(f'peer_{self.serverPort}_card.pkl', connectionSocket)
                    my_ip = self.get_private_ip()
                    self.send_message(F"UPDATE_PEER_CARD,{my_ip},{self.serverPort},{self.card}", self.net_ip, int(self.net_port))


                elif sentence.startswith("RESPONSE_FROM_SEARCH"):
                    _, server_address, server_port, card = sentence.split(',')
                    my_ip = self.get_private_ip()
                    trade_request = f"TRADE_REQUEST,{my_ip},{self.serverPort},{self.card}"
                    self.send_message(trade_request, server_address, int(server_port))

                elif sentence.startswith("NET_SEARCH"):
                    _, sender_ip, sender_port, wanted_card = sentence.split(',')
                    if wanted_card == self.card:
                        my_ip = self.get_private_ip()
                        response = f"RESPONSE_FROM_SEARCH,{my_ip},{self.serverPort},{self.card}"
                        self.send_message(response, sender_ip, int(sender_port))

                    elif not self.list_of_peers:
                        my_ip = self.get_private_ip()
                        response = f"FAIL_RESPONSE_FROM_SEARCH,{my_ip},{self.serverPort}"
                        self.send_message(response, sender_ip, int(sender_port))

                    else:
                        flag = 0
                        for peer in self.list_of_peers:
                            if peer.card == wanted_card:
                                print(f"Found a peer with the card: {wanted_card}.")
                                response = f"NET_SEARCH,{sender_ip},{sender_port},{wanted_card}"
                                self.send_message(response, peer.serverAddress, int(peer.serverPort))
                                flag = 1
                                break
                        if flag == 0:
                            my_ip = self.get_private_ip()
                            response = f"FAIL_RESPONSE_FROM_SEARCH,{my_ip},{self.serverPort}"
                            self.send_message(response, sender_ip, int(sender_port))

                else:
                    capitalizedSentence = sentence.upper()
                    connectionSocket.send(capitalizedSentence.encode())

                connectionSocket.close()
                break
            except Exception as e:
                print(f"Error handling message: {e}")
                continue


    def send_message(self, message, server_name, server_port):
        try:
            clientSocket = socket(AF_INET, SOCK_STREAM)
            clientSocket.connect((server_name, server_port))
            clientSocket.send(message.encode())
            modifiedSentence = clientSocket.recv(1024)
            clientSocket.close()
        except Exception as e:
            print(f"Error sending message: {e}")

    def propose_trade(self, server_port, server_adress):
        proposed_card = input("Enter the card you want to propose for trade: ")
        my_ip = self.get_private_ip()
        trade_request = f"TRADE_REQUEST,{my_ip},{self.serverPort},{proposed_card}"
        self.send_message(trade_request, server_adress, server_port)

    def ask_to_network(self,wanted_card): # aqui é pra enviar a msg pro peer2 que o peer1 tem na lista e ver se a carta eh realmente essa
        try:
            my_ip = self.get_private_ip()
            network_search_messsage = f"NET_SEARCH,{my_ip},{self.serverPort},{wanted_card}"
            for peer in self.list_of_peers:
                if peer.card == wanted_card:
                    print(f"Found a peer with the card: {wanted_card}.")
                    self.send_message(network_search_messsage, peer.serverAddress, int(peer.serverPort))
                    return
            print(f"Not Found a peer with the card {wanted_card}.")
        except Exception as e:
            print(f"Error asking to network: {e}")
           
    
    def process_trade_requests(self):
        while True:
            try:
                if not self.trade_requests.empty():
                    sender_ip,sender_port, proposed_card = self.trade_requests.get()
                    response = input(f"\nTrade request from {sender_ip}:{sender_port} . Swap your card {self.card} with {proposed_card}? (yes/no): ")
                    if response.lower() == 'yes':
                        my_ip = self.get_private_ip()
                        confirmation_message = f"TRADE_CONFIRM,{my_ip},{self.serverPort},{self.card}"
                        self.send_file_and_message(f'peer_{self.serverPort}_card.pkl', confirmation_message, sender_ip, int(sender_port))
                        old_card = self.card
                        self.card = proposed_card

                        #vamos criar o objetopeer e adicionar na lista de peers
                        traded_peer = objectPeer(sender_ip,sender_port,old_card)
                        self.list_of_peers.append(traded_peer)
                        print(f"Card traded. New card: {self.card}")
                        self.send_message(F"UPDATE_PEER_CARD,{my_ip},{self.serverPort},{self.card}", self.net_ip, int(self.net_port))
                        break
                    
                    else:
                        print("Trade rejected.")
                        reject_message = f"TRADE_REJECTED,{self.serverPort},{self.card}"
                        self.send_message(reject_message, "localhost", int(sender_port))
                        break
                else:
                    print("No trade requests to process.")
                    break
            except Exception as e:
                print(f"Error processing trade requests: {e}")
                continue

    def send_file_and_message(self, file_name, message, server_name, server_port):
        try:
            with socket(AF_INET, SOCK_STREAM) as s:
                s.connect((server_name, server_port))
                s.send(message.encode())
                with open(file_name, 'rb') as f:
                    data = f.read()
                    s.sendall(data)
        except Exception as e:
            print(f"Error sending file and message: {e}")

            
    def send_file(self, file_name, server_name, server_port):
        try:
            with socket(AF_INET, SOCK_STREAM) as s:
                s.connect((server_name, server_port))
                with open(file_name, 'rb') as f:
                    data = f.read()
                    s.sendall(data)
        except Exception as e:
            print(f"Error sending file: {e}")
    def receive_file(self, file_name, connectionSocket):
        try:
            with open(file_name, 'wb') as f:
                while True:
                    data = connectionSocket.recv(1024)
                    if not data:
                        break
                    f.write(data)
        except Exception as e:
            print(f"Error receiving file: {e}")
            
    def get_private_ip(self):
        s = socket(AF_INET, SOCK_DGRAM)
        try:
            # Conecta-se a um endereço não alcançável fora da rede para descobrir o IP local.
            s.connect(("10.254.254.254", 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip

def show_menu(peer):
    private_ip = peer.get_private_ip()
    print(f"Peer ready to receive messages.")
    print(f"Private IP: {private_ip}, Port: {peer.serverPort}")
    
    
    while True:
        print("\nMenu:")
       
        
        print(f"Your card: {peer.card}")
        print("1. Send message")
        print("2. Propose trade")
        print("3. Propose trade w/ network search")
        print("4. Process trade requests")
        print("5. Refresh menu")
        print("6. Connect to network")
        print("7. Lista de peers")
        print("8. Exit")
        choice = input("Enter your choice: ")
        
        if choice == '1':
            message = input("Enter the message: ")
            server_port = int(input("Enter the server port: "))
            server_adress = input("Enter the server adress: ") # localhost se for no mesmo pc, senao vai ter q botar o ip do cell
            peer.send_message(message, server_adress, server_port)
        elif choice == '2':
            server_port = int(input("Enter the server port to propose trade: "))
            server_adress = input("Enter the server adress: ")
            peer.propose_trade(server_port, server_adress)
        elif choice == '3':
            wanted_card = input("Enter the card you want to trade: ")
            peer.ask_to_network(wanted_card)
            continue
            
        elif choice == '4':
            peer.process_trade_requests()
            
        elif choice == '5':
            continue
        
        elif choice == '6':
            peer_ip= peer.get_private_ip()
            message = f"CONNECT_TO_NETWORK,{peer_ip},{int(peer.serverPort)},{peer.card}"
            server_port = int(input("Enter the server port: "))
            server_adress = input("Enter the server adress: ") # localhost se for no mesmo pc, senao vai ter q botar o ip do cell
            peer.send_message(message, server_adress, server_port)
            
        elif choice == '7':
            for peer1 in peer.list_of_peers:
                print(peer1.serverAddress, peer1.serverPort, peer1.card)
                print("\n")
            continue    
                   
        
        elif choice == '8':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    port = int(input("Enter the port number for this peer: "))
    peer = Peer(port)
    show_menu(peer)