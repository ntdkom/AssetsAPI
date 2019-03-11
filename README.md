# New Asset API

Rest API which aims at keeping track of newly provisioned systems.
The following auto-actions are performed:
- schedule the Qualys vulnerability scan 
- verify if Splunk universal forwarder is installed and registered in one of the Splunk Deployment servers.

Installation steps for Debian

```bash
# Update/Upgrade server
apt-get update
apt-get upgrade -y

# Install dependencies
sudo apt-get install -y mongodb-org=3.6.10 mongodb-org-server=3.6.10 mongodb-org-shell=3.6.10 mongodb-org-mongos=3.6.10 mongodb-org-tools=3.6.10
sudo apt-get install -y python3-pip gunicorn3 nginx
sudo pip3 install gunicorn falcon mongoengine pymongo falcon_jsonify arrow hvac requests

# Deliver source code to the target server

# Configure Hashicorp Vault to store API token at the following location:
/secret/assetsapi/apitoken
# Configure Hashicorp Vault to store password for the local assets database at the following location:
/secret/assetsapi/localdb/assetsdb
# Configure Hashicorp Vault to store password for the Qualys database at the following location:
/secret/assetsapi/qualys/qualysdb
# Configure Hashicorp Vault to store password for the Splunk deployment servers at the following location:
/secret/assetsapi/splunkds/splunkapi

# Generate the Vault token and insert it into the assetsapi.service file
sudo sed -i 's/Environment=\"VAULT_TOKEN=\"/Environment=\"VAULT_TOKEN=token_here\"/g' assetsapi.service

# Install service file
sudo mv assetsapi.service /etc/systemd/system/
sudo systemctl daemon-reload

# Configure nginx, make sure to specify proper IP address in assetsapi.conf
sudo rm /etc/nginx/sites-available/default
sudo rm /etc/nginx/sites-enabled/default
sudo mv assetsapi.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/assetsapi.conf /etc/nginx/sites-enabled/assetsapi.conf

# Place source code into the /opt/assets-api
sudo mkdir /opt/assets-api
sudo chown www-data:www-data /opt/assets-api -R

# Generate ssl cert for nginx
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/nginx/ssl/nginx-selfsigned.key -out /etc/nginx/ssl/nginx-selfsigned.cer

# Start the services:
sudo systemctl restart nginx
sudo systemctl restart assetsapi

```
