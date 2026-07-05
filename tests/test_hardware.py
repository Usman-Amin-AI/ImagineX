import types

from modules.hardware import classify_runtime_backend, get_backend_compatibility_matrix


class DummyTorch:
    version = types.SimpleNamespace(hip=None, cuda=None)

    class backends:
        class mps:
            @staticmethod
            def is_available():
                return False


def test_classifies_rocm_when_hip_runtime_is_present():
    torch_module = types.SimpleNamespace(
        version=types.SimpleNamespace(hip="6.0", cuda=None),
        backends=types.SimpleNamespace(mps=types.SimpleNamespace(is_available=lambda: False)),
    )

    backend = classify_runtime_backend(torch_module=torch_module, platform_name="Linux")

    assert backend["backend"] == "rocm"
    assert backend["support"] == "supported"


def test_classifies_directml_on_windows_when_requested():
    backend = classify_runtime_backend(
        torch_module=DummyTorch,
        platform_name="Windows",
        directml_available=True,
    )

    assert backend["backend"] == "directml"
    assert backend["support"] == "supported"


def test_compatibility_matrix_marks_supported_backends():
    matrix = get_backend_compatibility_matrix()

    assert matrix["cuda"]["support"] == "supported"
    assert matrix["rocm"]["support"] == "supported"
    assert matrix["directml"]["support"] == "supported"
    assert matrix["mps"]["support"] == "supported"
