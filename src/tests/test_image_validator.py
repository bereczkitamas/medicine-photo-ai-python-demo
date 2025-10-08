import pytest

from app.validation.image_validator import ImageValidator


@pytest.fixture()
def validator() -> ImageValidator:
    # Use a typical allowed set (lowercase, as in AppConfig)
    return ImageValidator({".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"})


def test_allows_known_extensions_case_insensitive_filename(validator: ImageValidator) -> None:
    assert validator.allowed_file("photo.PNG") is True
    assert validator.allowed_file("scan.JpEg") is True
    assert validator.allowed_file("animation.GIF") is True


def test_rejects_unknown_extensions(validator: ImageValidator) -> None:
    assert validator.allowed_file("document.pdf") is False
    assert validator.allowed_file("archive.zip") is False


def test_filename_without_extension_is_rejected(validator: ImageValidator) -> None:
    assert validator.allowed_file("noext") is False
    assert validator.allowed_file("anothername") is False


def test_multi_dot_filename_uses_last_extension(validator: ImageValidator) -> None:
    assert validator.allowed_file("backup.photo.jpeg") is True
    assert validator.allowed_file("backup.photo.jpeg.old") is False


def test_leading_dot_files(validator: ImageValidator) -> None:
    # os.path.splitext(".png") returns ("", ".png")
    assert validator.allowed_file(".png") is False
    # unrelated dotfile without allowed ext
    assert validator.allowed_file(".gitignore") is False


def test_trailing_dot_results_in_no_extension(validator: ImageValidator) -> None:
    assert validator.allowed_file("weird.") is False


def test_allowed_set_is_respected_without_internal_normalization() -> None:
    # If caller provides mixed-case allowed entries, they are treated literally because
    # ImageValidator only lowercases the filename, not the allowed set.
    v = ImageValidator({".PNG"})
    # filename lowercased ext is ".png" which is not in {".PNG"}
    assert v.allowed_file("file.PNG") is False
    # sanity: if allowed set includes lowercase too, it passes
    v2 = ImageValidator({".PNG", ".png"})
    assert v2.allowed_file("file.PNG") is True
