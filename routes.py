from app import api
from resources.newserver import NewServerResource

api.add_route('/assets/api/newserver', NewServerResource())