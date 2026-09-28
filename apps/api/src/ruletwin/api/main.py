from ruletwin.api.app import create_app
from ruletwin.config import get_settings

app = create_app(get_settings())
