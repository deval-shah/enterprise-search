from dependency_injector import containers, providers
from llamasearch.pipeline import PipelineFactory

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    pipeline_factory = providers.Singleton(PipelineFactory, is_api_server=True)