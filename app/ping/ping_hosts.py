from re import search
from ipaddress import ip_address
from socket import gethostbyname
from subprocess import call


def host_ping(host):
    address = ip_address(gethostbyname(host) if search('[a-zA-Z]', host) else host)
    output = open("/dev/null")
    return call(['ping', '-c', '1', str(address)], stdout=output, stderr=output)


if __name__ == '__main__':
    list_ip = ['yandex.ru', 'www.mail.ru', 'www.google.com', '198.168.1.12', '100.2.15.3', '5.5.5.5']
    for item in list_ip:
        stat = host_ping(item)
        print(f'Узел {item}{"" if stat == 0 else " не"} доступен')