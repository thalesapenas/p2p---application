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
        
        self.list_of_peers = []
        self.trades_counter = 0
        self.listen_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
        self.listen_thread.start()


    def listen_for_messages(self):
        while True:
            connectionSocket, addr = self.serverSocket.accept()
            print(f"Connection from {addr}")
            threading.Thread(target=self.handle_message, args=(connectionSocket,), daemon=True).start()

    def handle_message(self, connectionSocket):
        while True:
            try:
                sentence = connectionSocket.recv(1024).decode()
                if not sentence:
                    continue

                print("\nReceived message:", sentence)
                
                if sentence.startswith("CONNECT_TO_NETWORK"):
                    _, peer_ip, peer_port, peer_card = sentence.split(',')
                    print(f"A New peer connected to the network: {peer_ip}, {peer_port}, {peer_card}")
                    new_peer = objectPeer(peer_ip, peer_port, peer_card)
                    self.list_of_peers.append(new_peer)
                    
                elif sentence.startswith("UPDATE_PEER_CARD"):
                    _, peer_ip, peer_port, peer_card = sentence.split(',')
                    print(f"Peer {peer_ip}:{peer_port}; updated card to {peer_card}")
                    for peer in self.list_of_peers:
                        if peer.serverAddress == peer_ip and peer.serverPort == peer_port:
                            peer.card = peer_card
                            break
                    self.trades_counter += 1


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
            print("Response from server:", modifiedSentence.decode())
            clientSocket.close()
        except Exception as e:
            print(f"Error sending message: {e}")

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
    
    def send_list_of_peers(self):
        try:
            for peer in self.list_of_peers:
                # Crie uma lista de peers que exclui o peer atual
                peers_to_send = [p for p in self.list_of_peers if p.serverAddress != peer.serverAddress or p.serverPort != peer.serverPort]

                # Formate a mensagem contendo a lista de peers e as informações do servidor que está enviando
                my_ip = self.get_private_ip()
                message = f"LIST_PEERS_FROM:{my_ip}:{self.serverPort}:" + ",".join(f"{p.serverAddress}:{int(p.serverPort)}:{p.card}" for p in peers_to_send)

                self.send_message(message, peer.serverAddress, int(peer.serverPort))

        except Exception as e:
            print(f"Error sending list of peers: {e}")

def show_menu(peer):
    private_ip = peer.get_private_ip()
    print(f"Peer ready to receive messages.")
    print(f"Private IP: {private_ip}, Port: {peer.serverPort}")
    
    
    while True:
        print("\nMenu:")
        print("1. list of peers")
        print("2. Send list of peers")
        print("3. Refresh menu")
        print("4. Delete list of peers")
        print("5. Exit")
        choice = input("Enter your choice: ")
        
        if choice == '1':
            print("List of peers:")
            for p in peer.list_of_peers:
                print(f"{p.serverAddress}:{p.serverPort}:{p.card}")
            continue
            
        elif choice == '2':
            peer.send_list_of_peers()
            print("List of peers sent to all peers.")
                 
        elif choice == '3':
            continue

        elif choice == '4':
            peer.list_of_peers.clear()  
            print("List of peers deleted.")
            continue
        
        elif choice == '5':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")
        if peer.trades_counter == 5:
            print("Trade limit reached. Sending list of peers to all peers.")
            peer.send_list_of_peers()
            peer.trades_counter = 0 

if __name__ == "__main__":
    port = int(input("Enter the port number for this peer: "))
    peer = Peer(port)
    show_menu(peer)