import zmq
import json

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")

with open('files/names.txt', 'r') as json_file:
    data = json.load(json_file)

while True:
    message = socket.recv_multipart()
    if message[0] == b"upload":
        fname = message[1].decode("utf-8")
        client = message[3].decode("utf-8")
        recv_counter = int(message[4].decode("utf-8"))
        if data.get(client):
            tfname = fname
            if recv_counter == 0:
                while data[client].get(tfname):
                    socket.send_string('N')
                    tfname = socket.recv_string()
                fname = tfname
                name, ext = fname.split('.')
                data[client][fname] = name+'_'+client+'.'+ext
            with open('files/'+data[client][fname], 'ab') as f:
                f.write(message[2])
        else:
            name, ext = fname.split('.')
            data[client] = {fname: name+'_'+client+'.'+ext}
            with open('files/'+data[client][fname], 'wb') as f:
                f.write(message[2])

        with open('files/names.txt', 'w') as outfile:
            json.dump(data, outfile)
        socket.send_string("Uploaded")

    elif message[0] == b"list":
        files = []
        user = message[1].decode("utf-8")
        if data.get(user):
            for us in data[user]:
                print(us)
                files.append(us.encode("utf-8"))
        socket.send_multipart(files)
    elif message[0] == b"download":
        fname = message[1].decode('utf-8')
        client = message[2].decode('utf-8')
        if data.get(client):
            if data[client].get(fname):
                file = data[client][fname]
                with open('files/'+file, 'rb') as f:
                    bytes = f.read()
                    socket.send_multipart([bytes])
            else:
                socket.send_multipart([b"N"])
        else:
            socket.send_multipart([b"NC"])
