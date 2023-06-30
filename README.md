# Purpose

This is a PoC setup to demonstrate how to configure and transfer DICOM data
using Orthancs's [transfer accelerator plugin](https://book.orthanc-server.com/plugins/transfers.html).

# Description

This demo contains:

- A docker compose file that starts two Orthanc instances (Orthanc Foo and Orthanc Bar). Each instance is declared in the `OrthancPeers` configuration of the other; this configuration is also used by the accelarator plugin. They are both configured through environement variables only. It is also possible to start each Orthanc instance individually for demonstrations running on different machines.
 - To start both containers together:
    - To start, use `docker-compose up --build`, inside 'docker' folder.
    - To stop, use `docker-compose down`, inside 'docker' folder.
 - To start them individually:
    - To start the orthanc-foo instance, use `docker-compose up -f 'orthanc-foo.yml' --build`, inside 'docker' folder.
    - To start the orthanc-bar instance, use `docker-compose up -f 'orthanc-bar.yml' --build`, inside 'docker' folder. 

- A Python script, 'gateway-driver.py' (inside src folder) that monitors the 'Orthanc Foo' instance for changes and transfers these changes to the 'Orthanc Bar' instance.

# Running

- Connect to the `orthanc-foo` on [http://localhost:8043](http://localhost:8043) (username: foo / password: foo) if you want to monitor data
arriving in 'Orthanc Foo' instance

- Start the Gateway Driver: python3 src/gateway-driver.py localhost 8043 foo foo

- Upload a study to this instance of Orthanc from a DICOM viewer (e.g. Horos)(DICOM Port for Orthanc Foo is 4243).

When finished, the study should be available on the 'Orthanc Bar' instance:

- Open it to check `orthanc-bar` on [http://localhost:8044](http://localhost:8044) (username: bar / password: bar).

- Check that the study is stored and integrate there.