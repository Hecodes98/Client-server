import zmq
import sys
import math
from collections import deque

from hashlib import sha256
from hashlib import sha1

from os import listdir, getcwd
from os.path import isfile, join, getsize

PS = 1024*64  # 64KB
thisdir = getcwd()
dct_files = {f: 1 for f in listdir(thisdir) if isfile(join(thisdir, f))}
context = zmq.Context()


def code(string):
    return string.encode('utf-8')


def hash_transform(bytes, full_doc=False):
    return sha256(bytes).hexdigest() if full_doc else sha1(bytes).hexdigest()


def file_validation(fname):
    return dct_files.get(fname)


def send_parts(list_parts):
    for port in list_parts:
        socket = context.socket(zmq.REQ)
        socket.connect("tcp://localhost:"+str(port.decode('utf-8')))
        print(port.decode('utf8'), " ", len(list_parts[port]))
        for part in list_parts[port]:
            socket.send_multipart(
                [b'upload', code(part[0]), part[1]])
            socket.recv_multipart()
        socket.close()


def request(port, send_method='multipart', recv_method='multipart', list_params=[]):
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:"+str(port))
    response = None

    if send_method == 'multipart':
        socket.send_multipart(list_params)
    if send_method == 'json':
        socket.send_json(str(list_params[0]))

    if recv_method == 'multipart':
        response = socket.recv_multipart()
    if recv_method == 'json':
        response = socket.recv_json()

    socket.close()
    return response


def download_parts(dict_parts):
    hash_bytes = {}
    for port in dict_parts:
        print(port)
        socket = context.socket(zmq.REQ)
        socket.connect("tcp://localhost:"+port)
        for hash_part in dict_parts[port]:
            socket.send_multipart([b'download', code(hash_part)])
            btes = socket.recv_multipart()
            hash_bytes[hash_part] = btes[0]
        socket.close()
    return hash_bytes


def download(client, file_name):
    response = request(5555, list_params=[
                       b'client', b'download', code(file_name), code(client)])

    if response == b'NF':
        print("Archivo inexistente en el servidor")
    elif response == b'NC':
        print("Cliente inexistente")
    else:
        while file_validation(file_name):
            file_name = input(
                "Ya tienes un archivo con este nombre, por favor ingresa uno nuevamente")
        dict_connections = eval(response[0].decode('utf-8'))
        guide_connection = {}
        for server in dict_connections['server-list']:
            guide_connection[server] = []
        idx = 0
        # Average cases O(n), Worst Case O(2n) == O(n)
        for port in dict_connections['server-list']:
            guide_connection[port].append(dict_connections['hashes'][idx])
            idx += 1
        hash_bytes = download_parts(dict_parts=guide_connection)
        with open(file_name, 'wb') as f:
            for hsh in dict_connections['hashes']:
                f.write(hash_bytes[hsh])
                del hash_bytes[hsh]


def read_part(file_name, index):
    bytes = 0
    with open(file_name, 'rb') as f:
        f.seek(index*PS)
        bytes = f.read(PS)
    return bytes


def upload(client, file_name):

    if file_validation(file_name):
        hash_name = sha256()
        num_parts = math.ceil(getsize(file_name)/PS)
        print(num_parts)
        list_servers = request(5555, list_params=[
            b'client', b'upload'])
        num_servers = len(list_servers)
        # server_list = deque(response)
        server_parts = {}
        for part in list_servers:
            server_parts[part] = []
        with open(file_name, 'rb') as f:
            while True:
                part = f.read(PS)
                if not part:
                    break
                hash_name.update(part)
        response = request(5555, list_params=[b'client',
                                              b'check', code(hash_name.hexdigest()), code(client), code(file_name)])

        if response[0] == b'Y':
            print('Archivo creado')
            return

        dict_proxy = {
            "fname": file_name,
            "client": client,
            "hash": hash_name.hexdigest(),
            "list_hash": [None]*num_parts,
            "servers": [None]*num_parts
        }

        for i in range(len(list_servers)):
            port = list_servers[i].decode('utf-8')
            print(port)
            socket = context.socket(zmq.REQ)
            socket.connect("tcp://localhost:"+str(port))
            for j in range(i, num_parts, num_servers):
                part = read_part(file_name, index=j)
                hash_part = hash_transform(part)
                dict_proxy['list_hash'][j] = hash_part
                dict_proxy['servers'][j] = str(port)
                socket.send_multipart([b'upload', code(hash_part), part])
                socket.recv_multipart()
            socket.close()

        response = request(5555,
                           list_params=[b'client', b'update', str(dict_proxy).encode('utf-8')])
        print(response)
    else:
        print("Archivo no existente")


def list_files(client):
    response = request(5555, list_params=[b'client', b'list', code(client)])
    print('Tus archivos en tu servidor son los sigueintes: ')
    for file in response:
        print("- ", file.decode('utf-8'))


def main():
    try:
        cmd = sys.argv[1]
    except:
        print("Debes usar alguna accion: upload, list o download")
    if cmd == 'upload':
        upload(sys.argv[2], sys.argv[3])
    if cmd == 'download':
        download(sys.argv[2], sys.argv[3])
    if cmd == 'list':
        list_files(sys.argv[2])


if __name__ == "__main__":
    main()
