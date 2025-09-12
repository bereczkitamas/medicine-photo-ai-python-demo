from dependency_injector import containers, providers

from app import AppConfig


def build_container(app_config: type[AppConfig]):
    """Wire application components into a dependency-injector container."""
    from app.storage.filesystem import FileSystem
    from app.repository.image_repository import ImageRepository
    from app.validation.image_validator import ImageValidator
    from app.services.image_service import ImageService

    class Container(containers.DeclarativeContainer):
        config = providers.Object(app_config)

        # Base infrastructure
        fs = providers.Singleton(FileSystem)
        fs().ensure_storage(config().UPLOAD_DIR, config().METADATA_FILE)

        # Repositories and validators
        image_repository = providers.Factory(
            ImageRepository,
            metadata_file=config.provided.METADATA_FILE,
            fs=fs,
        )

        image_validator = providers.Factory(
            ImageValidator,
            allowed_extensions=config.provided.ALLOWED_EXTENSIONS,
        )

        # Services
        image_service = providers.Factory(
            ImageService,
            upload_dir=config.provided.UPLOAD_DIR,
            repo=image_repository,
            fs=fs,
            validator=image_validator,
        )

    return Container()
