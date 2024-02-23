# -*-coding:Utf-8 -*

"""
this tool is a proxy in python3. All code came from blackhat python 2nd edition
See argparse help in main for usage.
my modifications:
- func and var rename for camel case
- add some print
- replacing string format for python3 style.
- add doc string everywhere
- correct indentation in handler for receive first
- replacing args management by argparse func
- removing serverLoop useless function
- Handle HTTP with compression

to do:
- replace hexdump func by a display object to allow dump in file or display
- Add compression method support for http
"""

import argparse
import gzip
import socket
import sys
import textwrap
import threading

from pyPYPM import utils

HEX_FILTER = ''.join([(len(repr(chr(i))) == 3) and chr(i) or '.' for i in range(256)])
debugModeGlob = False
CONNECTION_TIMEOUT = 30


def manageArguments():
    """
    Function to parse arguments
    :return: a parse_args object
    """
    parser = argparse.ArgumentParser(
        description='BHP Proxy',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''Example: proxy.py -la 127.0.0.1 -lp 9000 -ra 10.12.132.1 -rp 9000 -rf True'''))
    parser.add_argument('-la', '--localAddress', default='127.0.0.1', help='The local address we listen on')
    parser.add_argument('-lp', '--localPort', default=8080, help='The local port we listen on.')
    parser.add_argument('-ra', '--remoteAddress', required=True, help='The remote address proxy replace')
    parser.add_argument('-rp', '--remotePort', type=int, required=True, help='specified port. 5555 by default.')
    parser.add_argument('-rf', '--receiveFirst', action='store_true', help='If remote send a banner, set it to True.')
    return parser.parse_args()


@utils.funcTimerDco(debugModeGlob)
def hexDump(src, length=16, show=True):
    """
    This function manage the display of the data captured between customer and remote
    to test: hexDump()
    :param src: the data to display in str or bytes utf-8.
    :param length: the lenght of each line to display.
    :param show: display or not.
    :return: a list named result
    """
    if isinstance(src, bytes):
        if src.startswith(b'HTTP'):
            header, http = manageHttp(src)
            src = header + http
        try:
            src = src.decode('utf-8')
        except UnicodeDecodeError as e:
            print(f"Hexdump error: {e}\n")
            return None
    results = list()
    for i in range(0, len(src), length):
        word = str(src[i:i+length])
        printable = word.translate(HEX_FILTER)
        hexa = ' '.join([f'{ord(c):02X}' for c in word])
        hexWidth = length * 3
        results.append(f'{i:04x}  {hexa:<{hexWidth}}  {printable}')
    if show:
        for line in results:
            print(line)
    else:
        return results


def findContentLen(byteObject: bytes)-> int:
    """
    Exctract content len from byte object
    :param byteObject: the object containing contentlen
    :return: a int
    """
    try:
        beginingIndex = byteObject.index(b'Content-Length')+len(b'Content-Length: ')
    except ValueError:
        raise ValueError('findContentLen cant find Content-Length: maybe call error?')
    delta = byteObject[beginingIndex:beginingIndex+10].find(b'\r')
    if byteObject[beginingIndex:beginingIndex+delta].decode().isdecimal():
        return int(byteObject[beginingIndex:beginingIndex+delta])
    else:
        raise ValueError('findContentLen cant find Content-Length: maybe call error?')


def manageHttp(message: bytes) -> tuple:
    """
    We will handle http special case
    :param message: the initial message
    :return: an uncompressed message
    """
    contantLen = findContentLen(message)
    hearderLen = len(message)-contantLen
    header = message[:hearderLen]
    httpCompressed = message[hearderLen:]
    compressionField = [i for i in header.decode().split('\r\n') if i.startswith('Content-Encoding:')]
    if len(compressionField) > 0:
        compressionMethod = compressionField[0].split(' ')[1]
    else:
        compressionMethod = ''
    if compressionMethod == 'gzip':
        http = gzip.decompress(httpCompressed)
    else:
        http = b'Uncompress Error'
    return header, http


@utils.funcTimerDco(debugModeGlob)
def proxyHandler(clientSocket: socket.socket, remoteHost: str, remotePort: int, receiveFirst=False):
    """
    This function will catch input trafic and transmit it after display. it call request and response handlers.
    :param clientSocket: a socket.socket object for client connection
    :param remoteHost: the remote host name or ip.
    :param remotePort: The remote port
    :param receiveFirst: If the remote start communication by sending baner, need to be set to True.
    :return: None
    """
    remoteSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remoteSocket.connect((remoteHost, remotePort))
    noTraficTimer = utils.Timer()
    try:
        inProgress = True
        if receiveFirst:
            remoteBuffer = receiveFrom(remoteSocket)
            hexDump(remoteBuffer)
            remoteBuffer = responseHandler(remoteBuffer)
            if len(remoteBuffer):
                print(f"\n[<==] Sending {len(remoteBuffer)} to client.")
                clientSocket.send(remoteBuffer)
        while inProgress:
            clientBuffer = receiveFrom(clientSocket)
            if len(clientBuffer):
                if noTraficTimer.started:
                    noTraficTimer.stop()
                line = f"\n[==>] Received {len(clientBuffer)} bytes from client."
                print(line)
                hexDump(clientBuffer)
                clientBuffer = requestHandler(clientBuffer)
                remoteSocket.send(clientBuffer)
                print("\n[==>] Sent to remote.")
            remoteBuffer = receiveFrom(remoteSocket)
            if len(remoteBuffer):
                if noTraficTimer.started:
                    noTraficTimer.stop()
                line = f"\n[<==] Received {len(remoteBuffer)} bytes from remote."
                print(line)
                hexDump(remoteBuffer)
                remoteBuffer = responseHandler(remoteBuffer)
                clientSocket.send(remoteBuffer)
                print("\n[<==] Sent to client.")
            if not len(clientBuffer) or not len(remoteBuffer):
                if noTraficTimer.started:
                    currentTimerState = noTraficTimer.current()
                    # print(f'No activity from {currentTimerState}')
                    if currentTimerState > CONNECTION_TIMEOUT:
                        print("\n[*] No more data. Closing connections.")
                        clientSocket.close()
                        remoteSocket.close()
                        noTraficTimer.stop()
                        print("[*] Connection closed.")
                        if noTraficTimer.started:
                            noTraficTimer.stop()
                        inProgress = False
                else:
                    noTraficTimer.start()

    except KeyboardInterrupt:
        remoteSocket.close()


@utils.funcTimerDco(debugModeGlob)
def receiveFrom(connection: socket.socket):
    """
    Manage reception of message from connection
    :param connection: a socket object connected
    :return: buffer containing data received
    """
    if not isinstance(connection, socket.socket):
        raise ValueError("Expecting a socket object here!")
    buffer = b''
    connection.settimeout(2)
    try:
        while True:
            data = connection.recv(4096)
            if not data:
                break
            buffer += data
    except Exception as e:
        pass
    return buffer


@utils.funcTimerDco(debugModeGlob)
def requestHandler(buffer):
    """
    A function to modify request before transmission to the remote. For now, it's empty
    :param buffer: a byte word to modify
    :return: modified byte word
    """
    return buffer


@utils.funcTimerDco(debugModeGlob)
def responseHandler(buffer):
    """
    A function to modify response before sending to client
    :param buffer: a byte word to modify
    :return: modified byte word
    """
    return buffer


def main():
    """
    Main functions
    :return: None
    """
    myArgs = manageArguments()

    localHost = myArgs.localAddress
    localPort = myArgs.localPort
    remoteHost = myArgs.remoteAddress
    remotePort = myArgs.remotePort
    receiveFirst = myArgs.receiveFirst
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind((localHost, int(localPort)))
    except Exception as e:
        print(f"Cant bind local ip/port: {e}")
        print(f"[!!] Failed to listen on IP {localHost}, port {localPort}!")
        print("[!!] Check for other socket or permissions.")
        sys.exit(2)
    print(f"listening on IP {localHost}:{localPort}")
    server.listen(5)
    clientSocket = ""
    try:
        while True:
            clientSocket, addr = server.accept()
            line = f">> Receiving incoming connection from {addr[0]}:{addr[1]}"
            print(line)
            proxyThread = threading.Thread(
                target=proxyHandler,
                args=(
                    clientSocket,
                    remoteHost,
                    int(remotePort),
                    receiveFirst
                )
            )
            proxyThread.start()
    except KeyboardInterrupt:
        if isinstance(clientSocket, socket.socket):
            clientSocket.close()
        server.shutdown(socket.SHUT_RDWR)
        server.close()
        print("[*] Server stopped!")
        exit(0)


if __name__ == '__main__':
    main()
