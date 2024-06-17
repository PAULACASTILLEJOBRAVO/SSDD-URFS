#!/usr/bin/python3

import sys
import binascii

import Ice
import argparse

Ice.loadSlice('urfs.ice')
import URFS

BLOCK_SIZE = 1024
DIR='./downloads'

class Client(Ice.Application):
    def run(self, argv):
        ic = self.communicator()
        properties = ic.getProperties()

        proxy_string = properties.getProperty(argv[1])
        proxy = ic.stringToProxy(proxy_string)
        try:
            self.frontend = URFS.FrontendPrx.checkedCast(proxy)
        except Ice.NotRegisteredException:
            print("Error. No se pudo localizar el frontend a partir del proxy introducido")
            return
        except Ice.ObjectNotExistException:
            print("Error. No se pudo localizar el frontend a partir del proxy introducido")
            return
        except Ice.ConnectionRefusedException:
            print("Error. No se pudo localizar el frontend a partir del proxy introducido")
            return
        
        if not self.frontend:
            raise RuntimeError('Invalid proxy')
        
        if ARGS.upload:
            self.upload_request(ARGS.upload)
        if ARGS.download:
            self.download_request(ARGS.download)
        if ARGS.remove:
            self.remove_request(ARGS.remove)
        if ARGS.list:
            self.list_request()

    def upload_request(self, file_name):
        try:
            uploader = self.frontend.uploadFile(file_name)
        except URFS.FileNameInUseError:
            print('File name already in use\n', flush=True)
            return

        with open(file_name, 'rb') as _file:
            while True:
                data = _file.read(BLOCK_SIZE)
                if not data:
                    uploader.send("")
                    break
                data = str(binascii.b2a_base64(data, newline=False))
                uploader.send(data)

        try:
            file_info = uploader.save()
        except URFS.FileAlreadyExistsError as e:
            print(f'File already exists: {e.hash}\n', flush=True)
            uploader.destroy()
            return

        uploader.destroy()
        print('Upload finished!', flush=True)
        print(f'{file_info.name}: {file_info.hash}\n', flush=True)
        
    def download_request(self, file_hash):    
        try:
            downloader = self.frontend.downloadFile(file_hash)
        except URFS.FileNotFoundError:
            print('File not found\n', flush=True)
            return
        
        try:
            file = self.frontend.getFileInfo(file_hash)
        except URFS.FileNotFoundError:
            print('File not found\n', flush=True)
            return
        
        file = file.name
        
        f = open('{}/{}'.format(DIR,file), 'wb')
        while True:
            data = downloader.recv(BLOCK_SIZE)
            if not data:
                break
            datadecode = binascii.a2b_base64(data[1:])
            f.write(datadecode)
        f.close()
        
        downloader.destroy()
        print('Download finished!\n', flush=True)
            
    def remove_request(self, file_hash):
        try:
            self.frontend.removeFile(file_hash)
        except URFS.FileNotFoundError:
            print('File not found\n', flush=True)
            return
        
        print('File eliminated\n')
        
    def list_request(self):
        file_list = self.frontend.getFileList()
        print("**************************")
        print('File list:', flush=True)
        print("-----------")
        for file in file_list:
            print(f'{file.name}: {file.hash}', flush=True)
        print('**************************\n')
if __name__ == '__main__':
    my_parser = argparse.ArgumentParser()
    my_group = my_parser.add_mutually_exclusive_group(required=False)

    my_group.add_argument('-u', '--upload',
        help='Upload a file to the system, given its path',
        action='store',
        type=str,)
    my_group.add_argument('-d', '--download',
        help='Download a file from the system, given its hash',
        action='store',
        type=str,)
    my_group.add_argument('-r', '--remove',
        help='Remove a file from the system, given its hash',
        action='store',
        type=str,)
    my_group.add_argument('-l', '--list',
        help='List all files in the system',
        action='store_true',
        default=False)

    ARGS, unknown = my_parser.parse_known_args()
    sys.exit(Client().main(sys.argv))