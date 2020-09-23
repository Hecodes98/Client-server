import zmq
import json
import sys
try:
    port = sys.argv[1]
    folder = sys.argv[2]
except:
    print("Porfavor indica el puerto de conexion de este servidor")

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:"+str(port))


def send_information_proxy(port):
    socket_proxy = context.socket(zmq.REQ)
    socket_proxy.connect("tcp://localhost:5555")
    socket_proxy.send_multipart([b'server', str(port).encode('utf-8')])
    print(socket_proxy.recv_multipart())
    socket_proxy.close()


def upload(hash_part, part_bytes):
    print(folder)
    with open(folder+'/'+str(hash_part.decode('utf-8')), 'wb') as f:
        f.write(part_bytes)


def download(hash_part):
    with open(folder+'/'+str(hash_part.decode('utf-8')), 'rb') as f:
        bytes = f.read()
    return bytes


def main():

    send_information_proxy(port)
    print("Socket Created")
    while True:
        request = socket.recv_multipart()
        action = request[0]
        print(action)
        if action == b'upload':
            upload(hash_part=request[1], part_bytes=request[2])
            socket.send_multipart([b'Part uploaded'])
        if action == b'download':
            bytes = download(hash_part=request[1])
            socket.send_multipart([bytes])


if __name__ == "__main__":
    main()
