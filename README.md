# SSDD-URFS

## Nivel
Básico

## Modo de ejecución:
### Esencial:
- make start
- make test-client

### Varios servidores: 
- make run-icestorm
- make run-registry
- make run-filemanager FILEMANAGER_PROXY=filemanager1 FILEMANAGER_ADAPTER=FileManagerAdapter1
- make run-filemanager FILEMANAGER_PROXY=filemanager2 FILEMANAGER_ADAPTER=FileManagerAdapter2

<br>
<br>

- make run-frontend FRONTEND_PROXY=frontend1 FRONTEND_CALL_FILEMANAGER_PROXY=FileManager1.Proxy FRONTEND_ADAPTER=FrontendAdapter1
- make run-client-upload CLIENT_CALL_FRONTEND_PROXY=Frontend1.Proxy
- make run-client-list CLIENT_CALL_FRONTEND_PROXY=Frontend1.Proxy

<br>
<br>

- make run-frontend FRONTEND_PROXY=frontend2 FRONTEND_CALL_FILEMANAGER_PROXY=FileManager1.Proxy FRONTEND_ADAPTER=FrontendAdapter2
- make run-client-remove CLIENT_CALL_FRONTEND_PROXY=Frontend2.Proxy
- make run-client-list CLIENT_CALL_FRONTEND_PROXY=Frontend2.Proxy

<br>
<br>

- make run-frontend FRONTEND_PROXY=frontend3 FRONTEND_CALL_FILEMANAGER_PROXY=FileManager2.Proxy FRONTEND_ADAPTER=FrontendAdapter3
- make run-client-upload CLIENT_CALL_FRONTEND_PROXY=Frontend3.Proxy
- make run-client-download CLIENT_CALL_FRONTEND_PROXY=Frontend3.Proxy
- make run-client-remove CLIENT_CALL_FRONTEND_PROXY=Frontend3.Proxy
- make run-client-list CLIENT_CALL_FRONTEND_PROXY=Frontend3.Proxy
