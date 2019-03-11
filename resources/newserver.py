import falcon
import settings
import re
import hvac
import os
import xml.etree.ElementTree as etree
import urllib
import datetime
from pymongo import MongoClient
import requests
from requests.auth import HTTPBasicAuth
from model import NewServer

# Before serving request, validate IPv4 server's address and supplied emails.
def validate_request_data(req, resp, resource, params):
    ip_pattern = re.compile("^[\d+]+\.[\d+]+\.[\d+]+\.[\d+]+$")
    email_pattern = re.compile("[a-zA-Z0-9._-]+@[a-zA-Z0-9-]\.[a-z]")
    if not (ip_pattern.match(req.get_json('network', dtype=str)) and email_pattern.match(req.get_json('owner', dtype=str)) and email_pattern.match(req.get_json('builder', dtype=str))):
        msg = 'You supplied the wrong IP or email address.'
        raise falcon.HTTPBadRequest('Bad request', msg)

@falcon.before(validate_request_data)
class NewServerResource(object):
    def on_post(self, req, resp):
        name = req.get_json('name', dtype=str, min=3, max=32)
        net = req.get_json('network', dtype=str, min=8, max=16)
        owner = req.get_json('owner', dtype=str, min=8, max=64)
        builder = req.get_json('builder', dtype=str, min=8, max=64)
        timestamp = req.get_json('timestamp', dtype=str, min=10, max=20)
        location = req.get_json('location', dtype=str, min=3, max=64)
        template = req.get_json('template', dtype=str, min=3, max=64)

        row = NewServer(
            srv_name = name,
            srv_network = net,
            srv_owner = owner,
            srv_builder = builder,
            srv_create_timestamp = timestamp,
            srv_location = location,
            srv_template = template
        )
        row.save()
        record_flag = True

        # Getting credentials from Vault
        try:
            vclient = hvac.Client(url=settings.VAULT['ADDR'], token=os.environ['VAULT_TOKEN'], verify=False)
            qualys_data = vclient.read('/secret/assetsapi/qualys')
            qualys = qualys_data["data"]["qualysdb"]
            splunkds_data = vclient.read('/secret/assetsapi/splunkds')
            splunkds = splunkds_data["data"]["splunkapi"]
            aux_checks_flag = True
            vclient.logout()
        except:
            aux_checks_flag = False

        if aux_checks_flag == True:
            # Prepare connection to the Qualys scanner database
            q_srv = settings.QUALYSDB['HOST']
            q_port = settings.QUALYSDB['PORT']
            q_db = settings.QUALYSDB['DATABASE']
            q_uname = urllib.parse.quote_plus(settings.QUALYSDB['USERNAME'])
            q_pass = urllib.parse.quote_plus(qualys)
            qualys_scan_flag = False
            scan = {"job_name": name,
                "targets": [ { "_cls" : "Target", "address" : str(net) } ],
                "date": datetime.datetime.utcnow(),
                "actor": { "_cls" : "Actor", "username" : "Assets API", "mail" : builder },
                "job_status": "Queued",
                "scan_refs": [],
                "reports": [],
                "reports_id": [],
                "emails_sent" : False}
            try:
                client = MongoClient('mongodb://%s:%s@%s:%s/default_db?authSource=%s' % (q_uname, q_pass, q_srv, q_port, q_db))
                db = client[q_db]
                col = db.job
                qualys_scan_flag = col.insert_one(scan).inserted_id
            except:
                pass

            # Prepare calls to the Splunk Deployment Servers` API
            dses = settings.SPLUNK['ADDRS']
            uname = settings.SPLUNK['USERNAME']
            tag_pattern = re.compile(".*totalResults")
            ds_flag = False
            for ds in dses:
                conn_str = 'https://{}:8089/services/deployment/server/clients?search=ip%3D{}'.format(ds, net)
                try:
                    splunk_reply = requests.get(conn_str, auth=HTTPBasicAuth(uname, splunkds), verify=False, timeout=10)
                except:
                    pass
                if (splunk_reply.status_code == 200):
                    xml_splunk_resp = etree.fromstring(splunk_reply.content)
                    for child in xml_splunk_resp:
                        if tag_pattern.match(child.tag) and child.text == '1':
                            ds_flag = True
        else:
            ds_flag = qualys_scan_flag = 'none'
                        
        # Constructing the response JSON
        resp.json = {"asset_saved": str(record_flag), 
                "aux_checks": [ { "performed": str(aux_checks_flag), "registered_in_splunk": str(ds_flag), "vulnerability_scan": str(qualys_scan_flag) } ] }
        resp.status = falcon.HTTP_201