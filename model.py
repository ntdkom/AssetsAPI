from mongoengine import *

class NewServer(Document):
    srv_name = StringField(required=True, max_length=32)
    srv_network = StringField(required=True, max_length=16)
    srv_owner = StringField(required=True, max_length=64)
    srv_builder = StringField(required=True, max_length=64)
    srv_create_timestamp = DateTimeField(required=True)
    srv_location = StringField(required=True, max_length=12)
    srv_template = StringField(required=True, max_length=64)