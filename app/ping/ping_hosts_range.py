from ipaddress import ip_address, ip_network
from socket import gethostbyname
from subprocess import call
from re import search
from threading import Thread


def host_ping(host, result):
    output = open("/dev/null")
    result[host] = call(['ping', '-c', '1', str(host)], stdout=output, stderr=output)


if __name__ == '__main__':
    host = input('Введите хост или адрес: ')
    address = ip_address(gethostbyname(host) if search('[a-zA-Z]', host) else host).compressed.split('.')
    address[3] = '0'
    address = '.'.join(address)
    subnet = ip_network(str(address) + '/24')

    executors = []
    result = dict()

    for host in subnet.hosts():
        thread = Thread(target=host_ping, args=[host, result])
        thread.start()
        executors.append(thread)

    for item in executors:
        item.join()

    for host in result.keys():
        print(f'Узел {host}{"" if result[host] == 0 else " не"} доступен')