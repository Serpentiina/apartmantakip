from flask import Blueprint

# Blueprint'leri tanımla
main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)
aidat = Blueprint('aidat', __name__)
gider = Blueprint('gider', __name__)
rapor = Blueprint('rapor', __name__)

# Route modüllerini import et
from app.routes.main import *
from app.routes.auth import *
from app.routes.aidat import *
from app.routes.gider import *
from app.routes.rapor import *
