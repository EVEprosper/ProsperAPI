
from prosper.publicAPI import create_app
#from prosper.publicAPI.crest_endpoint import create_app

@pytest.fixture
def app():
    app = create_app()
    return app
