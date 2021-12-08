from bioimageio.spec.model import raw_nodes


def test_load_raw_model(unet2d_nuclei_broad_any):
    from bioimageio.spec import load_raw_resource_description

    raw_model = load_raw_resource_description(unet2d_nuclei_broad_any)
    assert raw_model


def test_load_raw_model_fixed_shape(unet2d_fixed_shape):
    from bioimageio.spec import load_raw_resource_description

    raw_model = load_raw_resource_description(unet2d_fixed_shape)
    assert raw_model


def test_load_raw_model_diff_output_shape(unet2d_diff_output_shape):
    from bioimageio.spec import load_raw_resource_description

    raw_model = load_raw_resource_description(unet2d_diff_output_shape)
    assert raw_model


def test_load_raw_model_multi_tensor(unet2d_multi_tensor):
    from bioimageio.spec import load_raw_resource_description

    raw_model = load_raw_resource_description(unet2d_multi_tensor)
    assert raw_model


def test_load_raw_model_hpa(hpa_model):
    from bioimageio.spec import load_raw_resource_description

    raw_model = load_raw_resource_description(hpa_model)
    assert raw_model


def test_load_raw_model_stardist(stardist_model):
    from bioimageio.spec import load_raw_resource_description

    raw_model = load_raw_resource_description(stardist_model)
    assert raw_model


def test_load_raw_model_unet2d_keras_tf(unet2d_keras_tf):
    from bioimageio.spec import load_raw_resource_description

    raw_model = load_raw_resource_description(unet2d_keras_tf, update_to_format="latest")
    assert isinstance(raw_model, raw_nodes.Model)
    # test attachments
    assert len(raw_model.attachments.files) == 1
    assert (raw_model.root_path / raw_model.attachments.files[0]).exists()


def test_load_raw_model_to_format(unet2d_nuclei_broad_before_latest):
    from bioimageio.spec import load_raw_resource_description

    format_targets = [(0, 3), (0, 4)]
    format_version = tuple(map(int, unet2d_nuclei_broad_before_latest["format_version"].split(".")[:2]))

    for target in format_targets:
        if format_version <= target:
            to_format = ".".join(map(str, target))
            raw_model = load_raw_resource_description(unet2d_nuclei_broad_before_latest, update_to_format=to_format)
            assert raw_model.format_version[: raw_model.format_version.rfind(".")] == to_format
