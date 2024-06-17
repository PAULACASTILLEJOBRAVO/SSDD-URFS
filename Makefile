#!/usr/bin/make -f

NUM_FILEMANAGERS ?= 2
FILE ?= example.png
FILE_HASH ?= $(shell md5sum $(FILE) | cut -d' ' -f1)

FRONTEND_PROXY ?= frontend1
CLIENT_CALL_FRONTEND_PROXY ?= Frontend1.Proxy
FRONTEND_ADAPTER ?= FrontendAdapter1

FILEMANAGER_PROXY ?= filemanager1
FRONTEND_CALL_FILEMANAGER_PROXY ?= FileManager1.Proxy
FILEMANAGER_ADAPTER ?= FileManagerAdapter1

start:
	$(MAKE) run-icestorm & $(MAKE) run-registry &
	sleep 1
	$(MAKE) run-filemanager &
	sleep 1
	$(MAKE) run-frontend

run-filemanager:
	mkdir -p storage
	./FileManager.py --Ice.Config=filemanager1.config $(FILEMANAGER_PROXY) $(FILEMANAGER_ADAPTER)

run-frontend:
	./Frontend.py --Ice.Config=frontend1.config $(NUM_FILEMANAGERS) $(FRONTEND_PROXY) $(FRONTEND_CALL_FILEMANAGER_PROXY) $(FRONTEND_ADAPTER)

test-client:
	mkdir -p downloads
	./Client.py --Ice.Config=client.config $(CLIENT_CALL_FRONTEND_PROXY) --upload $(FILE) 
	./Client.py --Ice.Config=client.config $(CLIENT_CALL_FRONTEND_PROXY) --list 
	./Client.py --Ice.Config=client.config $(CLIENT_CALL_FRONTEND_PROXY) --download $(FILE_HASH) 
	./Client.py --Ice.Config=client.config $(CLIENT_CALL_FRONTEND_PROXY) --remove $(FILE_HASH) 
	./Client.py --Ice.Config=client.config $(CLIENT_CALL_FRONTEND_PROXY) --list 
run-icestorm:
	mkdir -p IceStorm/
	icebox --Ice.Config=icebox.config

run-registry:
	mkdir -p data/db/registry
	icegridregistry --Ice.Config=registry.config

clean:
	$(RM) -r downloads/ storage/ __pycache__/ URFS/
	$(RM) urfs_ice.py *.pyc

vclean: clean
	$(RM) -r IceStorm/ data/

run-client-upload:
	./Client.py --Ice.Config=client.config $(CLIENT_CALL_FRONTEND_PROXY) --upload $(FILE) 

run-client-download:
	mkdir -p downloads
	./Client.py --Ice.Config=client.config $(CLIENT_CALL_FRONTEND_PROXY) --download $(FILE_HASH) 

run-client-remove:
	./Client.py --Ice.Config=client.config $(CLIENT_CALL_FRONTEND_PROXY) --remove $(FILE_HASH)  

run-client-list:
	./Client.py --Ice.Config=client.config $(CLIENT_CALL_FRONTEND_PROXY) --list 