import zmq
import sys

from os import listdir, getcwd
from os.path import isfile, join

PS = (1024**2)*10

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")

thisdir = getcwd()
dct_files = {f: 1 for f in listdir(thisdir) if isfile(join(thisdir, f))}

cmd = sys.argv[1]
client = sys.argv[2]
fname = sys.argv[3] if len(sys.argv) > 3 else 'name'

sender_counter = 0

if cmd == "upload":
    if dct_files.get(fname):
        with open(fname, 'rb') as f:
            while True:
                part = f.read(PS)  # Esta línea está maldita
                print("part")
                if not part:
                    break  # The bytes were not read
                socket.send_multipart([b"upload", fname.encode(
                    'utf-8'), part, client.encode('utf-8'), str(sender_counter).encode("utf-8")])
                resp = socket.recv_string()
                while resp == 'N':
                    fname = input("Nombre ya existente, ingrese uno nuevo: ")
                    socket.send_string(fname)
                    resp = socket.recv_string()
                print(resp)
                sender_counter += 1
    else:
        print("Archivo no existente")
elif cmd == "download":
    socket.send_multipart(
        [b"download", fname.encode('utf-8'), client.encode("utf-8")])
    message = socket.recv_multipart()
    if message[0] == b"N":
        print("Archivo no encontrado")
    elif message[0] == b"NC":
        print("Cliente no encontrado")
    else:
        while dct_files.get(fname):
            fname = input(
                "Ya tienes este archivo, por favor indica otro nombre: ")
        with open(fname, 'wb') as f:
            f.write(message[0])
elif cmd == "list":
    socket.send_multipart([b'list', client.encode("utf-8")])
    files = socket.recv_multipart()
    for file in files:
        print(file.decode("utf-8"))
