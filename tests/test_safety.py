from PIL import Image

from modules.safety import sanitize_images_for_output


def test_safety_filter_is_off_by_default_and_keeps_image():
    image = Image.new('RGB', (4, 4), color='red')
    result = sanitize_images_for_output([image], enabled=False)
    assert len(result) == 1
    assert result[0].getpixel((0, 0)) == (255, 0, 0)


def test_safety_filter_can_replace_image_when_enabled(monkeypatch):
    image = Image.new('RGB', (4, 4), color='red')

    def fake_censor(images):
        return [Image.new('RGB', (4, 4), color='black')]

    monkeypatch.setattr('modules.safety._run_censor', fake_censor)
    result = sanitize_images_for_output([image], enabled=True)
    assert len(result) == 1
    assert result[0].getpixel((0, 0)) == (0, 0, 0)
