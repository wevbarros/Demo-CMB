#!/usr/bin/python
# -*- coding: utf-8 -*-

# Orthanc - A Lightweight, RESTful DICOM Store
# Copyright (C) 2012-2016 Sebastien Jodogne, Medical Physics
# Department, University Hospital of Liege, Belgium
# Copyright (C) 2017-2023 Osimis S.A., Belgium
# Copyright (C) 2021-2023 Sebastien Jodogne, ICTEAM UCLouvain, Belgium
# Copyright (C) 2023-2023 Victor Medeiros, iLIKA-UFPE, Brazil
#
# This program is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# This sample code shows how to setup a high-performance DICOM
# auto-routing through Orthancs's Transfers Accelerator Plugin from Osimis .
# All the DICOM instances that arrive inside Orthanc will be sent to a remote
# Orthanc Peer. A producer-consumer pattern is used.
#
# NOTE: This sample only works with Orthanc >= 0.5.2. Make sure that
# Orthanc was built with "-DCMAKE_BUILD_TYPE=Release" to get the best
# performance.

import queue
import sys
import time
import threading
import json

import RestToolbox as RestToolbox

## Print help message

if len(sys.argv) != 6:
    print("""
Sample script that continuously monitors the arrival of new DICOM
images into Orthanc (through the Changes API).

Usage: %s [hostname] [HTTP port] [username] [password] [orthanc peer name]
For instance: %s 127.0.0.1 8042 foo bar orthanc-foo 
""" % (sys.argv[0], sys.argv[0]))
    exit(-1)

URL = 'http://%s:%d' % (sys.argv[1], int(sys.argv[2]))
RestToolbox.SetCredentials(sys.argv[3], sys.argv[4])
peer_name = sys.argv[5]

# Queue that is shared between the producer and the consumer
# threads. It holds the instances that are still to be sent.
queue = queue.Queue()

# The producer thread. It monitors the arrival of new instances into
# Orthanc, and pushes their ID into the shared queue. This code is
# based upon the "ChangesLoop.py" and "HighPerformanceAutoRouting.py"
# sample code.

def Producer(queue):
    current = 0

    while True:
        r = RestToolbox.DoGet(URL + '/changes', {
            'since' : current,
            'limit' : 4   # Retrieve at most 4 changes at once
            })

        for change in r['Changes']:
            # We are only interested in the arrival of new instances
            if change['ChangeType'] == 'NewInstance':
                queue.put(change['ID'])

        current = r['Last']

        if r['Done']:
            time.sleep(1)

# The consumer thread. It continuously reads the instances from the
# queue, and send them to the remote Orthanc peer. Each time a packet of
# instances is sent, a single DICOM connexion is used, hence improving
# the performance.
def Consumer(queue):
    TIMEOUT = 0.1
    
    while True:
        instances = []
        while True:
            try:
                # Block for a while, waiting for the arrival of a new
                # instance
                instance = queue.get(True, TIMEOUT)

                # A new instance has arrived: Record its ID
                instances.append(instance)
                queue.task_done()

            except Exception as e:
                break

        if len(instances) > 0:
            request_body = {}
            request_body['Resources'] = []
            request_body['Compression'] = "gzip"
            request_body['Peer'] = peer_name
            for instance in instances:
                 request_body['Resources'].append({"Level":"Instance","ID":instance})
            print('Sending a packet of %d instances' % len(instances))
            start = time.time()

            # Send current instances through the Tranfers Accelerator Plugin REST API
            RestToolbox.DoPost('%s/transfers/send' % URL, json.dumps(request_body))

            # TODO: We use the Pull strategy from Transfers Accelerator Plugin 
            # (ref: https://book.orthanc-server.com/plugins/transfers.html#sending-in-pull-vs-push-mode)
            # that make requests of the instances from the peer to improve performance.
            # We will have to implement a delete task just after the transfer finish.
            #
            # Remove all the instances from Orthanc
            # for instance in instances:
            #     RestToolbox.DoDelete('%s/instances/%s' % (URL, instance))

            # Clear the log of the exported instances (to prevent the
            # SQLite database from growing indefinitely). More simply,
            # you could also set the "LogExportedResources" option to
            # "false" in the configuration file since Orthanc 0.8.3.
            RestToolbox.DoDelete('%s/exports' % URL)

            end = time.time()
            print('The packet of %d instances has been sent in %d seconds' % (len(instances), end - start))


# Thread to display the progress
def PrintProgress(queue):
    while True:
        print('Current queue size: %d' % (queue.qsize()))
        time.sleep(1)

# Start the various threads
progress = threading.Thread(None, PrintProgress, None, (queue, ))
progress.daemon = True
progress.start()

producer = threading.Thread(None, Producer, None, (queue, ))
producer.daemon = True
producer.start()

consumer = threading.Thread(None, Consumer, None, (queue, ))
consumer.daemon = True
consumer.start()

# Active waiting for Ctrl-C
while True:
    time.sleep(0.1)