import zmq
import json


context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")
# 0 : sender
# 1-server : port
# 1 - client : method


def de_encode(string, option):
    return string.encode('utf-8') if option == 'en' else string.decode('utf-8')


def load_json(file_name):
    data = {}
    with open('proxy/'+file_name, 'r') as json_file:
        data = json.load(json_file)
    return data


def write_json(file_name, content):
    with open('proxy/'+file_name, 'w') as outfile:
        json.dump(content, outfile)


def assignation(dict_to_assign):
    list_to_return = []
    for item in dict_to_assign:  # O(cantidad de keys) -> keys < 5 === O(1)
        list_to_return.append(dict_to_assign[item])
    return list_to_return


def main():
    clients = load_json('clients.json')
    files = load_json('files.json')
    list_servers = []

    while True:
        res = socket.recv_multipart()
        sender = res[0]
        if sender == b'server':
            list_servers.append(int(res[1].decode('utf-8')))
            socket.send_multipart([b'Added'])
        elif sender == b'client':
            method = res[1]
            if method == b'upload':
                send_list = []
                for item in list_servers:
                    send_list.append(str(item).encode('utf-8'))
                socket.send_multipart(send_list)
            if method == b'update':
                json_client = eval(res[2].decode('utf-8'))
                fname, client, hash_client, hashes, servers = assignation(
                    json_client)
                if not clients.get(client):
                    clients[client] = {
                        fname: hash_client}
                else:
                    clients[client][fname] = hash_client

                files[hash_client] = {
                    'server-list': servers, 'hashes': hashes}
                write_json('clients.json', clients)
                write_json('files.json', files)
                socket.send_multipart([b'updated'])
            if method == b'check':
                hash_file = res[2].decode('utf-8')
                client = res[3].decode('utf-8')
                name_file = res[4].decode('utf-8')
                # TODO Mismo nombre de arcvhivo del cliente con diferente hash
                if files.get(hash_file):
                    if clients.get(client):
                        clients[client][name_file] = hash_file
                    else:
                        print('pase aqui')
                        clients[client] = {name_file: hash_file}
                        write_json('clients.json', clients)
                    socket.send_multipart([b'Y'])
                else:
                    print('Respuesta CHECK')
                    print(res)
                    socket.send_multipart([b'N'])
            if method == b'download':
                name_file = res[2].decode('utf-8')
                client = res[3].decode('utf-8')
                if clients.get(client):
                    if clients[client].get(name_file):
                        hash_file = clients[client][name_file]
                        dict_send = files[hash_file]
                        socket.send_multipart([str(dict_send).encode('utf-8')])
                    else:
                        socket.send_multipart([b'NF'])
                else:
                    socket.send_multipart([b'NC'])
            if method == b'list':
                client = res[2].decode('utf-8')
                files = list()
                for file in clients[client]:
                    files.append(file.encode('utf-8'))

                socket.send_multipart(files)


if __name__ == "__main__":
    main()
