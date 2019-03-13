# New Asset API

Rest API which aims at keeping track of newly provisioned systems.
The following auto-actions are performed:
- save new assets's information into the local database;
- schedule the Qualys vulnerability scan;
- verify if Splunk universal forwarder is installed and registered in one of the Splunk Deployment servers.

## Usage

### Information that should be submitted in the form of JSON:

| Field | Description |
| --- | --- |
| name | short name of the system |
| network | IPv4 address of the system |
| owner | Email address of the owner of asset, this address will be used to send Security-related requests |
| builder | Email address of the responsible person who built the system. Initial vulnerability scan report is sent to it |
| timestamp | Timestamp when the system got provisioned. Format: `YYYY-MM-DD HH:MM` |
| location | Short annotation of the system's location |
| template | Name of the template used to provision system, it should include the OS name |

### Invocation example

New asset is being saved into the database:

```bash
curl --request POST https://securityinventory.local/assets/api/newserver \
--header "Authorization: $APITOKEN" --header "Account-ID: assetsapi" --header "Content-Type: application/json"  \
--data \
"
{
\"name\":\"K8S-MGMT\",
\"network\":\"10.10.22.11\",
\"owner\":\"pe@company.com\",
\"builder\":\"john@company\",
\"timestamp\":\"2019-02-25 12:12\",
\"location\":\"Virginia datacenter\",
\"template\":\"Debian 9 x86-64\"
}"
```

API replies with JSON:

```
{"asset_saved": "True", "aux_checks": [{"vulnerability_scan": "5c755ada29c81f3d5abd548d", "registered_in_splunk": "True", "performed": "True"}]}
```


## Installation steps for Debian

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
