import zmq
import sys

from os import listdir, getcwd
from os.path import isfile, join

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")
thisdir = getcwd()
dct_files = {f: 1 for f in listdir(thisdir) if isfile(join(thisdir, f))}


cmd = sys.argv[1]
client = sys.argv[2]
fname = sys.argv[3] if len(sys.argv) > 3 else 'name'

if cmd == "upload":
    with open(fname, 'rb') as f:
        bytes = f.read()  # Esta línea está maldita
        socket.send_multipart([b"upload", fname.encode(
            'utf-8'), bytes, client.encode('utf-8')])
        resp = socket.recv_string()
        while resp == 'N':
            nameis = input("Nombre ya existente, ingrese uno nuevo: ")
            socket.send_string(nameis)
            resp = socket.recv_string()
        print(resp)
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
