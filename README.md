# ezshare
Easy way to share files through net.
Based on ```http.server```.

### **WARNING**
There is no authorization here, so anyone who can see your device can also download/upload files.  
You can specify server mode: allow only download or only upload (see [arguments](#arguments)).

### Installation
    python3 setup.py install

### Usage
    ezshare

then open ```<local-ip>:<port>``` from other device.

To shutdown server use ```^c```.

Download files - by clicking on the file name.  
Upload file - on separate page (link 'upload file' at the top of the page).  
Files will be uploaded to the root directory, regardless of current viewed directory.

### Arguments
ezshare [-h] [--share-only | --upload-only] [--port n] [path]

    path               share/upload root directory
    -h, --help         show this help message and exit
    --share-only, -s   disable upload function
    --upload-only, -u  disable share function
    --port n, -p n     Specify alternate port [default: 8000]

### Supported version
Tested under python3.5, python3.7