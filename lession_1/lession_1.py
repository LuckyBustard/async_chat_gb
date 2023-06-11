# 1.
s1='разработка'
s2='сокет'
s3='декоратор'
print(type(s1))
print(type(s2))
print(type(s3))
print (s1,s2,s3)
s1_u=u'\u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0430'
s2_u=u'\u0441\u043e\u043a\u0435\u0442'
s3_u=u'\u0434\u0435\u043a\u043e\u0440\u0430\u0442\u043e\u0440'
print(type(s1_u),type(s2_u),type(s3_u))
print(s1_u, s2_u, s3_u)


# 2. 
p1=b'class'
p2=b'function'
p3=b'method'
print(type(p1),type(p2),type(p3))
print(p1, p2, p3)


# 3.
for s in ['attribute','класс','функция','type']:
    try:
        print(s,type(s),s.encode('ascii'), ' - encoding to bytes successful ')
    except:
        print(s,type(s),' - not valid input for bytes string')


# 4.
for s in ['разработка','администрирование','protocol','standard']:
    p=s.encode('utf-8','replace')
    q=p.decode('utf-8')
    print(s,p,q)


# 5. 
import subprocess
for sites in ['yandex.ru','youtube.com']:
  args=['ping',sites]
  subproc_ping=subprocess.Popen(args,stdout=subprocess.PIPE)
  for line in subproc_ping.stdout:
  #    print(line)
      print(line.decode('cp866').encode('utf-8').decode('utf-8'))


# 6.
import locale
def_co=locale.getpreferredencoding()
print(def_co)
f=open('file.txt','w')
f.writelines(['сетевое программирование\n', 'сокет\n', 'декоратор\n'])
print(f)
f.close()
#выдает <_io.TextIOWrapper name='file.txt' mode='w' encoding='cp1251'>
print(f)
#no error
with open('file.txt', encoding='cp1251') as f_n:
    for el_str in f_n:
        print(el_str)
# выдает ошибку, т.к. файл в другой кодировке:
# UnicodeDecodeError: 'utf-8' codec can't decode byte 0xf1 in position 0: invalid continuation byte
with open('file.txt', encoding='utf-8') as f_n:
    for el_str in f_n:
        print(el_str)
