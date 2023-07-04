import os
from subprocess import Popen, CREATE_NEW_CONSOLE

process = []

while True:
    action = input('Выберите действие: q - выход , s - запустить n клиентов, x - закрыть все окна:')

    if action == 'q':
        break
    elif action == 's':
        count = int(input('Введите необходимое количество клиентов:')) + len(process)
        for i in range(len(process), count):
            process.append(Popen(f'python {os.path.join(os.getcwd(), "client.py")} -n test{i}', creationflags=CREATE_NEW_CONSOLE))
    elif action == 'x':
        while process:
            sacrifice = process.pop()
            sacrifice.kill()
