#!/usr/bin/python3

import os
import sys
import binascii

import Ice

Ice.loadSlice('urfs.ice')
import URFS
import hashlib
import IceStorm
DIR = "./storage/"

class Downloader(URFS.Downloader):
    
    def __init__(self, hash):
        self.hash = hash
        self.total_size = 0
        self.file_pointer_position = 0 
    
    def recv(self, size, current=None): 
        for file in os.listdir(DIR):
            if self.hash == file: 
                with open('{}{}'.format(DIR,file), 'rb') as f:
                    data = f.read()
                    self.total_size = f.seek(0, os.SEEK_END)           
                
                    expand = min(self.file_pointer_position+size, self.total_size)
                    if self.file_pointer_position < self.total_size:
                            message = str(binascii.b2a_base64(data[self.file_pointer_position : expand], newline=False))
                            self.file_pointer_position = self.file_pointer_position + min(expand, size)
                            self.total_size = self.total_size - min(expand, size)
                            
                            return message
                        
                    else:
                        print("Finished task: download")
                        self.total_size = 0
                        self.file_pointer_position = 0 
                        f.close()
                        return ""
                             
    def destroy(self, current):
        current.adapter.remove(current.id)
        print(f'Destroy {current.id.name}', flush=True)

class FileManager(URFS.FileManager):   
    def __init__(self, broker, updater, file_data_dict):
        self.file_data_dict = file_data_dict
        self.broker = broker
        self.updater = updater
    def recogerDatos(self, fileManager):
        self.fileManager = fileManager
    def createUploader(self, filename, current=None):
        self.filename = filename
        servant = UploaderI(filename, self.broker, self.fileManager, self.updater, self.file_data_dict)
        proxy = current.adapter.addWithUUID(servant)
        return URFS.UploaderPrx.checkedCast(proxy)
    
    def createDownloader(self, hash, current=None):
        for file in os.listdir(DIR):
            if (hash == file):
                downloader = Downloader(hash)
                proxy = current.adapter.addWithUUID(downloader)
                return URFS.DownloaderPrx.checkedCast(proxy)
                   
        print(f"No file data found for hash {hash} ")
        raise URFS.FileNotFoundError()
        
    def removeFile(self, hash, current=None):
        if os.path.exists(DIR + hash):
            os.remove('{}{}'.format(DIR,hash))
            file_data = self.file_data_dict.get(hash)

            if file_data is not None:
                self.updater.removed(file_data)
            else:
                print(f"No file data found for hash {hash} in the list")
    
        else:
            raise URFS.FileNotFoundError()    
        
class UploaderI(URFS.Uploader):
    def __init__(self, filename, broker, fileManager, updater, file_data_dict):
        self.file_data_dict = file_data_dict
        self.filename = filename
        self.updater = updater
        self.data = None
        self.file_data = b''
        self.extension = os.path.splitext(filename)[1]
        self.broker = broker
        self.fileManager = fileManager
    def destroy(self, current=None):
        current.adapter.remove(current.id)
        print(f'Destroy {current.id.name}', flush=True)
    def send(self, data, current=None):
      if not data:
        with open(DIR + self.filename, 'wb') as file:
            file.write(self.file_data)
            print("File successfully reconstructed.")
        return
      else:
        block = data.replace("b'", "").replace("'", "")
        self.file_data += binascii.a2b_base64(block)
    def save(self, current=None):
        hash_md5 = hashlib.md5()

        # Abre el archivo en modo binario y calcula el hash MD5
        with open(DIR + self.filename, "rb") as file:
            # Lee el archivo en bloques para manejar archivos grandes
            for chunk in iter(lambda: file.read(4096), b""):
                hash_md5.update(chunk)
             # Devuelve el hash MD5 como una cadena hexadecimal
        md5_hash = hash_md5.hexdigest()
        new_file_name = DIR + md5_hash
         # Comprueba si el archivo existe
        if os.path.exists(new_file_name):
            os.remove(DIR + self.filename)
            raise URFS.FileAlreadyExistsError(f"File {new_file_name} already exists")
        os.rename(DIR + self.filename, new_file_name)
        
        file_info = URFS.FileInfo()
        file_info.name = self.filename
        file_info.hash = md5_hash

       ####################publisher
        file_data = URFS.FileData()
        file_data.fileInfo = file_info
        file_data.fileManager = URFS.FileManagerPrx.checkedCast(self.fileManager)
        if not file_data.fileManager:
            raise RuntimeError('Invalid proxy')
        self.file_data_dict[file_data.fileInfo.hash] = file_data

        self.updater.new(file_data)
        print("Finished task: upload")
        return file_info  

        
class Server(Ice.Application):  
    def get_topic_manager(self):
        key = 'IceStorm.TopicManager.Proxy'
        proxy = self.communicator().propertyToProxy(key)
        if proxy is None:
            print("property {} not set".format(key))
            return None
        print("Using IceStorm in: '%s'" % key)
        return IceStorm.TopicManagerPrx.checkedCast(proxy) 
    def run(self, argv):
        file_data_dict = {}
        topic_mgr = self.get_topic_manager()
        if not topic_mgr:
            print('Invalid proxy')
            return 2

        topic_name = "FileUpdatesTopic"
        try:
            topic = topic_mgr.create(topic_name)
        except IceStorm.TopicExists:
            topic = topic_mgr.retrieve(topic_name)

        publisher = topic.getPublisher()
        updater = URFS.FileUpdatesPrx.uncheckedCast(publisher)
        broker = self.communicator()
       
        servant = FileManager(broker, updater, file_data_dict)
        try:
            adapter = broker.createObjectAdapter(argv[2])
        except Ice.CommunicatorDestroyedException:
            print("Error. Comunicaciones destruidas")
            return    
        adapterUploader = broker.createObjectAdapter("UploaderAdapter")

        proxy = adapter.add(servant, broker.stringToIdentity(argv[1]))
        servant.recogerDatos(proxy)
        proxyUploader = adapterUploader.add(servant, broker.stringToIdentity("upload1"))
        
        print(proxy, "\n", proxyUploader, flush=True)
        try:
            adapter.activate()
        except Ice.ConnectionRefusedException:
            print("Error. Conexión denegada. Ejecute el registry")
            return 
        adapterUploader.activate()
        
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0

server = Server()
sys.exit(server.main(sys.argv))
