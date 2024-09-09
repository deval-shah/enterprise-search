from dependency_injector import containers, providers
from llamasearch.pipeline import PipelineFactory
from llamasearch.settings import config as app_config
from llamasearch.api.db.session import get_db, sessionmanager

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    pipeline_factory = providers.Singleton(PipelineFactory, config=app_config, is_api_server=True)
    db = providers.Resource(get_db)
    session_factory = providers.Callable(lambda: sessionmanager.session_factory)

container = Container()