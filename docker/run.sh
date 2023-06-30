#!/bin/bash



# Execute the original entrypoint script with the provided configuration file path
cd /
/docker-entrypoint.sh /tmp/orthanc.json &


# Install needed packages
apt-get update
apt-get upgrade -y

pip3 install httplib2 --upgrade
apt install openresolv 
apt install iproute2 -y 
apt-get install procps -y


# Install WireGuard
apt install wireguard -y
apt-get install wireguard -y


# Configure WireGuard interface
#mv /etc/wireguard/wg0.conf /etc/wireguard/wg0.conf.bak
cp /home/wg0.conf /etc/wireguard/wg0.conf


# Start WireGuard connection
wg-quick down wg0
wg-quick up wg0





# Start driver application (Gateway Driver)
exec python3 /home/src/gateway-driver.py 127.0.0.1 8042 foo foo orthanc-bar


