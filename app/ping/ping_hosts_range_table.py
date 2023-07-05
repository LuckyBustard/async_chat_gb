from ipaddress import ip_address, ip_network
from socket import gethostbyname
from subprocess import call
from re import search
from threading import Thread
from tabulate import tabulate


def host_ping(host, result):
    output = open("/dev/null")
    result[host] = call(['ping', '-c', '1', str(host)], stdout=output, stderr=output)


if __name__ == '__main__':
    host = input('Введите хост или адрес: ')
    address = ip_address(gethostbyname(host) if search('[a-zA-Z]', host) else host).compressed.split('.')
    address[3] = '0'
    address = '.'.join(address)
    subnet = ip_network(str(address) + '/24')

    result = dict()
    executors = []

    for host in subnet.hosts():
        thread = Thread(target=host_ping, args=[host, result])
        thread.start()
        executors.append(thread)

    for item in executors:
        item.join()

    formatted = {'REACHABLE': [], 'NOT_REACHABLE': []}
    for host in result.keys():
        formatted['REACHABLE' if result[host] == 0 else 'NOT_REACHABLE'].append(host)

    print(tabulate(formatted, headers='keys'))

