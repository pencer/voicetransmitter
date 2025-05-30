1. Setup
  $ pip3 install tornado # 6.4.2

  $ openssl genpkey -out web-server.key -algorithm RSA -pkeyopt rsa_keygen_bits:2048
  $ openssl req -new -key web-server.key -out web-server.csr
  $ openssl x509 -in web-server.csr -out web-server.crt -req -signkey web-server.key -days 365

1.1. Sample input for openssl setup (self signed certificate)

  Maybe the most important part is "Common Name".

    Country Name (2 letter code) [AU]:JP
    State or Province Name (full name) [Some-State]: YOUR_PROVINCE
    Locality Name (eg, city) []: YOUR_CITY
    Organization Name (eg, company) [Internet Widgits Pty Ltd]:Home
    Organizational Unit Name (eg, section) []:SOMETHING
    Common Name (e.g. server FQDN or YOUR name) []:YOUR_FQDN

2. Run
  
  $ python3 recv_wav.py

  Access to the server with "https://", port number 8000.

3. Auto start using systemctl

  Create a .service file, e.g.  /etc/systemd/system/voicetransmitter.service

  ```
  [Unit]
  Description=My Node.js Daemon

  [Service]
  User=pi
  Group=pi
  Environment="NODE_PATH=/usr/local/lib/node_modules"
  WorkingDirectory=/home/pi/work/voicetransmitter
  ExecStart=/usr/bin/python3 /home/pi/work/voicetransmitter/recv_wav.py
  Restart=always

  [Install]
  WantedBy=multi-user.target
  ```

  Enable the service

  $ sudo systemctl enable voicetransmitter

