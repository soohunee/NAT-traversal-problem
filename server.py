import sys
from socket import *
import threading
import pickle
import time

serverPort = 10080
rsize = 1024
registers = []
clients = set()
lock = threading.Lock()
def register_receive(sckt):
    global registers
    global clients
    while 1:
        data, addr = sckt.recvfrom(rsize)
        data = pickle.loads(data)
        
        if data['mode'] == 1:
            lock.acquire()
            temp = {'clientID' : data['clientID'], 'clientAddr' : addr,
                    'rcvTime':time.time(), 'privateIP' : data['privateIP']}
            
            for i in registers:
                if addr == i['clientAddr']:
                    i['rcvTime'] = time.time()
                    break
            else:
                print(temp['clientID']+'  '+str(temp['clientAddr'][0])+
                      ':'+str(temp['clientAddr'][1]))
                registers.append(temp)
                
                clients.add(addr)
                for client in clients:
                    sckt.sendto(pickle.dumps(registers), client)
                    
            lock.release()
        elif data['mode'] == 0:
            lock.acquire()
            for i in registers:
                if addr == i['clientAddr']:
                    print(i['clientID']+' is deregisterd  '+
                          str(i['clientAddr'][0])+
                      ':'+str(i['clientAddr'][1]))
                    registers.remove(i)
                    break
                    
            clients.remove(addr)
            for client in clients:
                sckt.sendto(pickle.dumps(registers), client)
            lock.release()
        

def client_timeout(sckt):
    global registers
    global clients
    rmv_list = list()
    while 1:
        lock.acquire()
        now = time.time()
        for r in registers:
            if now - r['rcvTime'] > 30:
                print(r['clientID']+' is disappeared  '+
                          str(r['clientAddr'][0])+
                      ':'+str(r['clientAddr'][1]))
                rmv_list.append(r)

        for i in rmv_list:
            registers.remove(i)
            clients.remove(i['clientAddr'])
            
        for client in clients:
                sckt.sendto(pickle.dumps(registers), client)
        rmv_list.clear()                
        lock.release()
        time.sleep(0.5)
        
def server():
    
    ss = socket(AF_INET, SOCK_DGRAM)
    ss.bind(("", serverPort))
    
    register_thread = threading.Thread(target=register_receive, args=(ss,))
    register_thread.start()
    
    client_timeout_thread = threading.Thread(target=client_timeout, args=(ss,))
    client_timeout_thread.start()
    
    

"""
Don't touch the code below
"""
if  __name__ == '__main__':
    server()


