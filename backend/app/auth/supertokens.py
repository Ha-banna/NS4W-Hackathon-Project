from supertokens_python import init, InputAppInfo, SupertokensConfig
from supertokens_python.recipe import emailpassword, session
from app.core.config import settings

def init_supertokens():
    init(
        app_info=InputAppInfo(
            app_name="Busted",
            api_domain=settings.API_DOMAIN,
            website_domain=settings.WEBSITE_DOMAIN,
            api_base_path=settings.API_BASE_PATH,
            website_base_path=settings.WEBSITE_BASE_PATH
        ),
        supertokens_config=SupertokensConfig(
            connection_uri=settings.SUPERTOKENS_CONNECTION_URI,
            api_key=settings.SUPERTOKENS_API_KEY
        ),
        framework='fastapi',
        recipe_list=[
	        session.init(), # initializes session features
            emailpassword.init()
        ],
        mode='asgi' # use wsgi if you are running using gunicorn
    )