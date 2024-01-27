# -*-coding:Utf-8 -*

"""
Code from Black Hat Python v2.
The purpose is to use paramiko module to execute command over ssh
See https://www.paramiko.org/
improvement:
- Validate the IP
- validate the port
- add password error management
- replace for loop by comprehension

To add/modify:
- key auth
- accept hostname
- Check if host name can be resolved
- review output
- add arguments managements

"""

import getpass
import paramiko

from pyPYPM import checkIfIp


# Functions
def sshCommand(ip: str, port: int, user: str, passwd: str, cmd: str) -> str:
    """
    The function executing the command
    :param ip:
    :param port:
    :param user:
    :param passwd:
    :param cmd:
    :return: the command result
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, port=port, username=user, password=passwd)
    except paramiko.ssh_exception.AuthenticationException:
        return f'Wrong password!'
    except paramiko.ssh_exception.NoValidConnectionsError:
        return f'Cant join IP {ip}!'
    _, stdout, stderr = client.exec_command(cmd)
    output = stdout.readlines() + stderr.readlines()
    if output:
        formatedOut = str([line.strip() for line in output])
        return formatedOut
    else:
        return f'No Output for {cmd}!'


def main():
    """
    Work in progress
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
    cmd = input('Enter command [id]:') or 'id'
    print(sshCommand(ip, port, user, password, cmd))


if __name__ == '__main__':
    main()
