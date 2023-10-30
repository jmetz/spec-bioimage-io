import datetime
import json
from pathlib import Path
from typing import Any, Dict, Iterable

import pooch
import pytest
from pydantic import AnyUrl

from bioimageio.spec._internal.constants import DISCOVER, LATEST
from bioimageio.spec._internal.types import FormatVersionPlaceholder
from tests.utils import ParameterSet, check_rdf

BASE_URL = "https://bioimage-io.github.io/collection-bioimage-io/"
RDF_BASE_URL = BASE_URL + "rdfs/"
WEEK = f"{datetime.datetime.now().year}week{datetime.datetime.now().isocalendar()[1]}"
CACHE_PATH = Path(__file__).parent / "cache" / WEEK


KNOWN_INVALID = {
    "10.5281/zenodo.5910854/6539073/rdf.yaml",
    "deepimagej/deepimagej/latest/rdf.yaml",
    "deepimagej/DeepSTORMZeroCostDL4Mic/latest/rdf.yaml",
    "deepimagej/Mt3VirtualStaining/latest/rdf.yaml",
    "deepimagej/MU-Lux_CTC_PhC-C2DL-PSC/latest/rdf.yaml",
    "deepimagej/SkinLesionClassification/latest/rdf.yaml",
    "deepimagej/SMLMDensityMapEstimationDEFCoN/latest/rdf.yaml",
    "deepimagej/UNet2DGlioblastomaSegmentation/latest/rdf.yaml",
    "deepimagej/WidefieldDapiSuperResolution/latest/rdf.yaml",
    "deepimagej/WidefieldFitcSuperResolution/latest/rdf.yaml",
    "deepimagej/WidefieldTxredSuperResolution/latest/rdf.yaml",
    "fiji/N2VSEMDemo/latest/rdf.yaml",
    "zero/Notebook_CycleGAN_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_DecoNoising_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_Detectron2_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_DRMIME_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_EmbedSeg_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_MaskRCNN_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_pix2pix_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_RetinaNet_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_StarDist_3D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_U-Net_2D_multilabel_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_U-Net_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_U-Net_3D_ZeroCostDL4Mic/latest/rdf.yaml",
}
KNOWN_INVALID_AS_LATEST = {
    "deepimagej/DeepSTORMZeroCostDL4Mic/latest/rdf.yaml",
    "deepimagej/Mt3VirtualStaining/latest/rdf.yaml",
    "deepimagej/WidefieldDapiSuperResolution/latest/rdf.yaml",
    "deepimagej/WidefieldFitcSuperResolution/latest/rdf.yaml",
    "deepimagej/DeepSTORMZeroCostDL4Mic/latest/rdf.yaml",
    "deepimagej/DeepSTORMZeroCostDL4Mic/latest/rdf.yaml",
    "deepimagej/DeepSTORMZeroCostDL4Mic/latest/rdf.yaml",
    "10.5281/zenodo.6559929/6559930/rdf.yaml",
    "10.5281/zenodo.7380171/7405349/rdf.yaml",
    "bioimageio/stardist/latest/rdf.yaml",
    "deepimagej/deepimagej-web/latest/rdf.yaml",
    "deepimagej/deepimagej/latest/rdf.yaml",
    "deepimagej/EVsTEMsegmentationFRUNet/latest/rdf.yaml",
    "deepimagej/MoNuSeg_digital_pathology_miccai2018/latest/rdf.yaml",
    "deepimagej/MU-Lux_CTC_PhC-C2DL-PSC/latest/rdf.yaml",
    "deepimagej/SkinLesionClassification/latest/rdf.yaml",
    "deepimagej/smlm-deepimagej/latest/rdf.yaml",
    "deepimagej/SMLMDensityMapEstimationDEFCoN/latest/rdf.yaml",
    "deepimagej/unet-pancreaticcellsegmentation/latest/rdf.yaml",
    "deepimagej/UNet2DGlioblastomaSegmentation/latest/rdf.yaml",
    "deepimagej/WidefieldTxredSuperResolution/latest/rdf.yaml",
    "fiji/Fiji/latest/rdf.yaml",
    "hpa/HPA-Classification/latest/rdf.yaml",
    "hpa/hpa-kaggle-2021-dataset/latest/rdf.yaml",
    "icy/icy/latest/rdf.yaml",
    "ilastik/arabidopsis_tissue_atlas/latest/rdf.yaml",
    "ilastik/cremi_training_data/latest/rdf.yaml",
    "ilastik/ilastik/latest/rdf.yaml",
    "ilastik/isbi2012_neuron_segmentation_challenge/latest/rdf.yaml",
    "ilastik/mitoem_segmentation_challenge/latest/rdf.yaml",
    "ilastik/mws-segmentation/latest/rdf.yaml",
    "imjoy/BioImageIO-Packager/latest/rdf.yaml",
    "imjoy/GenericBioEngineApp/latest/rdf.yaml",
    "imjoy/HPA-Single-Cell/latest/rdf.yaml",
    "imjoy/ImageJ.JS/latest/rdf.yaml",
    "imjoy/ImJoy/latest/rdf.yaml",
    "imjoy/LuCa-7color/latest/rdf.yaml",
    "imjoy/vizarr/latest/rdf.yaml",
    "qupath/QuPath/latest/rdf.yaml",
    "zero/Dataset_CARE_2D_coli_DeepBacs/latest/rdf.yaml",
    "zero/Dataset_CARE_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Dataset_CARE_3D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Dataset_CycleGAN_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Dataset_Deep-STORM_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Dataset_fnet_3D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Dataset_fnet_DeepBacs/latest/rdf.yaml",
    "zero/Dataset_Noise2Void_2D_subtilis_DeepBacs/latest/rdf.yaml",
    "zero/Dataset_Noise2Void_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Dataset_Noise2Void_3D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Dataset_Noisy_Nuclei_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Dataset_pix2pix_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Dataset_SplineDist_2D_DeepBacs/latest/rdf.yaml",
    "zero/Dataset_StarDist_2D_DeepBacs/latest/rdf.yaml",
    "zero/Dataset_StarDist_2D_ZeroCostDL4Mic_2D/latest/rdf.yaml",
    "zero/Dataset_StarDist_brightfield_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Dataset_StarDist_brightfield2_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Dataset_StarDist_Fluo_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Dataset_StarDist_fluo2_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Dataset_U-Net_2D_DeepBacs/latest/rdf.yaml",
    "zero/Dataset_U-Net_2D_multilabel_DeepBacs/latest/rdf.yaml",
    "zero/Dataset_YOLOv2_antibiotic_DeepBacs/latest/rdf.yaml",
    "zero/Dataset_YOLOv2_coli_DeepBacs/latest/rdf.yaml",
    "zero/Dataset_YOLOv2_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook Preview/latest/rdf.yaml",
    "zero/Notebook_Augmentor_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_CARE_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_CARE_3D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_Cellpose_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_CycleGAN_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_CycleGAN_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_DecoNoising_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_DecoNoising_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_Deep-STORM_2D_ZeroCostDL4Mic_DeepImageJ/latest/rdf.yaml",
    "zero/Notebook_Deep-STORM_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_DenoiSeg_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_Detectron2_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_Detectron2_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_DFCAN_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_DRMIME_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_DRMIME_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_EmbedSeg_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_EmbedSeg_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_fnet_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_fnet_3D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_Interactive_Segmentation_Kaibu_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_MaskRCNN_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_MaskRCNN_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_Noise2Void_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_Noise2Void_3D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_pix2pix_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_pix2pix_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_Quality_Control_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_RCAN_3D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_RetinaNet_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_RetinaNet_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_SplineDist_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_StarDist_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_StarDist_3D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_StarDist_3D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_U-Net_2D_multilabel_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_U-Net_2D_multilabel_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_U-Net_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_U-Net_2D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_U-Net_3D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_U-Net_3D_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/Notebook_YOLOv2_ZeroCostDL4Mic/latest/rdf.yaml",
    "zero/WGAN_ZeroCostDL4Mic.ipynb/latest/rdf.yaml",
}
EXCLUDE_FIELDS_FROM_ROUNDTRIP = {
    "10.5281/zenodo.7274275/8123818/rdf.yaml": {"inputs", "parent"},
    "zero/Notebook Preview/latest/rdf.yaml": {"rdf_source"},  # ' ' -> %20
}


def yield_rdf_paths() -> Iterable[ParameterSet]:
    cache_path: Any = pooch.retrieve(BASE_URL + "collection.json", None)
    with Path(cache_path).open(encoding="utf-8") as f:
        collection_data = json.load(f)["collection"]

    collection_registry: Dict[str, None] = {
        entry["rdf_source"].replace(RDF_BASE_URL, ""): None for entry in collection_data
    }
    collection = pooch.create(
        path=CACHE_PATH,
        base_url=RDF_BASE_URL,
        registry=collection_registry,
    )

    for rdf in collection_registry:
        rdf_path = Path(collection.fetch(rdf))
        rdf_key = rdf_path.relative_to(CACHE_PATH).as_posix()
        yield pytest.param(rdf_path, rdf_key, id=rdf_key)


@pytest.mark.parametrize("format_version", [DISCOVER, LATEST])
@pytest.mark.parametrize("rdf_path,rdf_key", list(yield_rdf_paths()))
def test_rdf(rdf_path: Path, rdf_key: str, format_version: FormatVersionPlaceholder):
    if (
        format_version == DISCOVER
        and rdf_key in KNOWN_INVALID
        or format_version == LATEST
        and rdf_key in KNOWN_INVALID_AS_LATEST
    ):
        pytest.skip("known failure")

    check_rdf(
        AnyUrl("https://example.com/"),
        rdf_path,
        as_latest=format_version == LATEST,
        exclude_fields_from_roundtrip=EXCLUDE_FIELDS_FROM_ROUNDTRIP.get(rdf_key, set()),
    )
