#!/usr/bin/python3

import sys
import os
import subprocess

import Ice
import IceStorm
Ice.loadSlice('urfs.ice')
import URFS

class FrontendI(URFS.Frontend):
    def __init__(self):
        self.fileManager = None
        self.diccionario = None
        self.file_data_list = []
        
    def nuevo(self, file):
        #hay que asegurarse de que el diccionario esté inicializado
        if self.diccionario is None:
            self.diccionario = {}
        # Usa el hash del archivo como clave y el nombre del archivo como valor
        self.diccionario[file.fileInfo.hash] = file.fileInfo.name         
        
        file_exists = False
        for file_data in self.file_data_list:
            if file_data.fileInfo.hash == file.fileInfo.hash:
                file_exists = True
                break

        if not file_exists:
         self.file_data_list.append(file)

    def eliminar(self, file):
        # Comprueba si el diccionario está inicializado y si contiene el archivo
        if self.diccionario is not None and file.fileInfo.hash in self.diccionario:
        # Elimina el archivo del diccionario
            del self.diccionario[file.fileInfo.hash]    
            
            for file_data in self.file_data_list:
                if file_data == file:
                    index = self.file_data_list.index(file_data)
                    del self.file_data_list[index]
            
    def createFileManager(self, broker, filemanagerProxy):
        properties = broker.getProperties()
        proxy = properties.getProperty(filemanagerProxy)

        proxy_fileManager = broker.stringToProxy(proxy)
        try:
            self.fileManager = URFS.FileManagerPrx.checkedCast(proxy_fileManager)
        except Ice.NotRegisteredException:
            print("Error. No se pudo localizar el filemanager a partir del proxy introducido")
            return
        except Ice.ObjectNotExistException:
            print("Error. No se pudo localizar el frontend a partir del proxy introducido")
            return
        except Ice.ConnectionRefusedException:
            print("Error. No se pudo localizar el frontend a partir del proxy introducido")
            return
        
        if self.fileManager is None:
            print('Invalid proxy')
    
    def downloadFile(self, hash, current=None):
        if self.diccionario is not None and hash in self.diccionario:
            download = self.fileManager.createDownloader(hash)
        else:
            print(f'No file data found for hash {hash}\n', flush=True)
            raise URFS.FileNotFoundError 
        return download
    
    def removeFile(self, hash, current=None):
        if self.diccionario is not None and hash in self.diccionario:
            print("Finished task: remove")
            self.fileManager.removeFile(hash)
        else:
            print(f'No file data found for hash {hash}\n', flush=True)
            raise URFS.FileNotFoundError 

    def uploadFile(self, name, current=None):
        if self.diccionario == None or len(self.diccionario) == 0:
            uploader = self.fileManager.createUploader(name)
        else:
            for fileupdate in self.diccionario:
                if self.diccionario[fileupdate] == name:
                    print(f'File name already in use\n', flush=True)
                    raise URFS.FileNameInUseError 
                else:
                    uploader = self.fileManager.createUploader(name)   
        return uploader
    
    def getFileInfo(self, hash, current=None):
        if self.diccionario is not None and hash in self.diccionario:
            file_info = URFS.FileInfo()
            file_info.hash = hash
            file_info.name = self.diccionario[hash]
            return file_info
        print("File not found in the list")
        raise URFS.FileNotFoundError
            
    
    def getFileList(self, current=None):
        # Inicializa una lista vacía para almacenar los FileInfo
        file_list = []
        # Comprueba si el diccionario está inicializado
        if self.diccionario is not None:
            # Itera sobre los elementos en el diccionario
            for clave, valor in self.diccionario.items():
                # Crea un nuevo FileInfo con el hash y el nombre del archivo
                file_info = URFS.FileInfo()
                file_info.hash = clave
                file_info.name = valor

                # Añade el FileInfo a la lista
                file_list.append(file_info)

        print("Finished task: list")
        # Devuelve la lista de FileInfo
        return file_list
    
    def replyNewFrontend(self, oldFrontend, current=None):
        print("\nIts frontend", oldFrontend)
        if len(self.file_data_list) != 0:
            print("\n",self.file_data_list)
    
class FrontendUpdatesI(URFS.FrontendUpdates):
    def __init__(self, broker, frontend):
        self.broker = broker
        self.frontend = frontend
        
    def get_topic_manager(self):
        key = 'IceStorm.TopicManager.Proxy'
        proxy = self.broker.propertyToProxy(key)
        if proxy is None:
            print("property {} not set".format(key))
            return None
        print("\nUsing IceStorm in: '%s'" % key)
        return IceStorm.TopicManagerPrx.checkedCast(proxy) 
    
    def newFrontend(self, newFrontend, current=None):
        print("\nNew frontend",newFrontend)
        
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
       
        if len(self.frontend.file_data_list) != 0:
            for file in self.frontend.file_data_list:
                fileInfo = file.fileInfo
                fileManager = file.fileManager
                fileData = URFS.FileData()
                fileData.fileInfo = fileInfo
                fileData.fileManager = fileManager
                updater.new(fileData)
        
        newFrontend.replyNewFrontend(newFrontend)
    
class FileUpdatesI(URFS.FileUpdates):
    def __init__(self, frontend):
        self.frontend = frontend
        
    def new(self, file, current=None):
        self.frontend.nuevo(file)
        
    def removed(self, file, current=None): 
        self.frontend.eliminar(file)
                
class Server(Ice.Application): 
    def get_topic_manager(self):
        key = 'IceStorm.TopicManager.Proxy'
        proxy = self.communicator().propertyToProxy(key)
        if proxy is None:
            print("property '{}' not set".format(key))
            return None

        print("\nUsing IceStorm in: '%s'" % key)
        return IceStorm.TopicManagerPrx.checkedCast(proxy)   
    def run(self, argv):
        broker = self.communicator()
        servant = FrontendI()
        try:
            adapter = broker.createObjectAdapter(argv[4])
        except Ice.CommunicatorDestroyedException:
            print("Error. Comunicaciones destruidas")
            return
        proxy_frontend = adapter.add(servant, broker.stringToIdentity(argv[2]))
       
        servant.createFileManager(broker, argv[3])
        if servant.fileManager == None:
            return
        ####################### subscriber

        topic_mgr = self.get_topic_manager()
        if not topic_mgr:
            print("Invalid proxy")
            return 2

        ic = self.communicator()
        
        #FILEUPDATES
        servantFileUpdates = FileUpdatesI(servant)
        adapterFileUpdates = ic.createObjectAdapter("FileUpdatesAdapter")
        subscriberFileUpdates = adapterFileUpdates.addWithUUID(servantFileUpdates)
        idFileUpdates = subscriberFileUpdates.ice_getIdentity()
        directProxyFileUpdates = adapterFileUpdates.createDirectProxy(idFileUpdates)
        topicNameFileUpdatee = "FileUpdatesTopic"
        try:
            topicFileUpdate = topic_mgr.create(topicNameFileUpdatee)
        except IceStorm.TopicExists:
            topicFileUpdate = topic_mgr.retrieve(topicNameFileUpdatee)
        topicFileUpdate.subscribeAndGetPublisher({}, directProxyFileUpdates)
        
        #FILEUPDATES
        servantFrontendUpdate = FrontendUpdatesI(broker, servant)
        adapterFrontendUpdate = ic.createObjectAdapter("FrontendUpdatesAdapter")
        subscriberF = adapterFrontendUpdate.addWithUUID(servantFrontendUpdate)
        idFrontendUpdates = subscriberF.ice_getIdentity()
        directProxyFrontendUpdate = adapterFrontendUpdate.createDirectProxy(idFrontendUpdates)
        topicNameFrontendUpdate = "FrontendUpdatesTopic"
        try:
            topicFrontendUpdates = topic_mgr.create(topicNameFrontendUpdate)
        except IceStorm.TopicExists:
            topicFrontendUpdates = topic_mgr.retrieve(topicNameFrontendUpdate)
            
        topicFrontendUpdates.subscribeAndGetPublisher({}, directProxyFrontendUpdate)
        
        print("\nWaiting events... '{}' and '{}'".format(directProxyFileUpdates, directProxyFrontendUpdate))
        
        adapterFileUpdates.activate()
        adapterFrontendUpdate.activate()
        try:
            adapter.activate()
        except Ice.ConnectionRefusedException:
            print("Error. Conexión denegada. Ejecute el registry")
            return 
        
        ####################### publisher
        id = proxy_frontend.ice_getIdentity()
        directProxy = adapter.createDirectProxy(id)
        frontend = URFS.FrontendPrx.checkedCast(directProxy)
        publisher = topicFrontendUpdates.getPublisher()
        fronter = URFS.FrontendUpdatesPrx.uncheckedCast(publisher)
        fronter.newFrontend(frontend)
        print("\nVersión de ICE:",Ice.stringVersion())
        ####################### end of publisher
        
        self.shutdownOnInterrupt()
        ic.waitForShutdown()

        topicFileUpdate.unsubscribe(subscriberFileUpdates)
        topicFrontendUpdates.unsubscribe(subscriberF)
        ####################### end of subscriber
        
        sys.stdout.flush()
        
        
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

      

server = Server()
if __name__ == '__main__':
    sys.exit(Server().main(sys.argv))