import sys
import subprocess
from socket import *
import threading
import pickle
import time

serverIP = '10.0.0.3'
serverPort = 10080
clientPort = 10081
serverAddr = (serverIP, serverPort)
ssize = 1024
privateIP = subprocess.check_output(['hostname', '-I']).decode()
privateIP = privateIP[:privateIP.index(' ')]
exit_flag = False
mypublicIP = ''
registers= []
lock = threading.Lock()
def register_send(sckt,serverAddr):
    global privateIP
    while 1:
        temp = {'clientID' : clientID, 'mode': 1, 'privateIP' : privateIP}
        sckt.sendto(pickle.dumps(temp), serverAddr)
        time.sleep(10)
    
def register_receive(sckt,clientID):
    global registers
    global mypublicIP
    while 1:
        data, addr = sckt.recvfrom(1024)
        data = pickle.loads(data)
        if type(data) == list:
            lock.acquire()
            registers = data
            for r in registers:
                if r['clientID'] == clientID:
                    mypublicIP = r['clientAddr'][0]
            lock.release()
        elif type(data) == dict:
            script = 'From '
            if data['nat'] == 'diff':
                for r in registers:
                    if addr == r['clientAddr']:
                        script += r['clientID']
                        break
            elif data['nat'] == 'same':
                for r in registers:
                    if addr[0] == r['privateIP']:
                        script += r['clientID']
                        break
            
            script += ' ['
            script += data['message']
            script += ']'
            print(script)
            
def instructions(sckt, clientPort):
    global mypublicIP
    global exit_flag
    global registers
    while 1:
        inst = input("")
        if inst == '@show_list':
            lock.acquire()
            for r in registers:
                print(r['clientID']+'  '+str(r['clientAddr'][0])+
                  ':'+str(r['clientAddr'][1]))
            lock.release()    
        elif inst == '@exit':
            temp = {'clientID' : clientID, 'mode': 0}
            sckt.sendto(pickle.dumps(temp), serverAddr)
            exit_flag = True
        elif inst.startswith('@chat'):
            lock.acquire()
            inst = inst[6:]
            sp = inst.index(' ')
            dst = inst[:sp]
            message = {'message' : inst[sp+1:], 'nat' : ''}
            for r in registers:
                if r['clientID'] == dst:
                    if r['clientAddr'][0] == mypublicIP:
                        dstIP = r['privateIP']
                        message['nat'] = 'same'
                        sckt.sendto(pickle.dumps(message), (dstIP,clientPort))
                    elif r['clientAddr'][0] != mypublicIP:
                        message['nat'] = 'diff'
                        dstIP = r['clientAddr']
                        sckt.sendto(pickle.dumps(message), dstIP)
                    break
            lock.release()
        else:
            print('wrong instruction retype')

def client(serverIP, serverPort, clientID):
    global exit_flag
    cs = socket(AF_INET, SOCK_DGRAM)
    cs.bind(("", clientPort))
    
    register_send_thread = threading.Thread(target=register_send, args=(cs,serverAddr))
    register_send_thread.daemon=True
    register_send_thread.start()
    
    register_receive_thread = threading.Thread(target=register_receive, args=(cs,clientID))
    register_receive_thread.daemon=True
    register_receive_thread.start()
    
    instructions_thread = threading.Thread(target=instructions, args=(cs,clientPort))
    instructions_thread.daemon=True
    instructions_thread.start()
    
    while exit_flag == False:
        pass
    sys.exit()
if  __name__ == '__main__':
    clientID = input("Enter ID : ")
    client(serverIP, serverPort, clientID)


