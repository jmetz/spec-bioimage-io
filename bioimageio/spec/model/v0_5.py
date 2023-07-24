import collections
from hashlib import sha256
import string
from typing import Annotated, Any, ClassVar, Dict, List, Literal, Optional, Set, Tuple, Union, get_args

from annotated_types import Ge, Gt, MaxLen, MinLen
from pydantic import AllowInfNan, FieldValidationInfo, field_validator, model_validator
from bioimageio.spec._internal._constants import SHA256_HINT

from bioimageio.spec._internal._utils import Field
from bioimageio.spec.shared.nodes import FrozenDictNode, Node
from bioimageio.spec.shared.types import (
    CapitalStr,
    FileSource,
    Identifier,
    NonEmpty,
    RawLeafValue,
    RawMapping,
    RawValue,
    LicenseId,
    Sha256,
    SiUnit,
    Version,
)
from bioimageio.spec._internal._validate import RestrictCharacters
from bioimageio.spec._internal._warn import warn
from bioimageio.spec import generic

from . import v0_4


# unit names from https://ngff.openmicroscopy.org/latest/#axes-md
SpaceUnit = Literal[
    "angstrom",
    "attometer",
    "centimeter",
    "decimeter",
    "exameter",
    "femtometer",
    "foot",
    "gigameter",
    "hectometer",
    "inch",
    "kilometer",
    "megameter",
    "meter",
    "micrometer",
    "mile",
    "millimeter",
    "nanometer",
    "parsec",
    "petameter",
    "picometer",
    "terameter",
    "yard",
    "yoctometer",
    "yottameter",
    "zeptometer",
    "zettameter",
]

TimeUnit = Literal[
    "attosecond",
    "centisecond",
    "day",
    "decisecond",
    "exasecond",
    "femtosecond",
    "gigasecond",
    "hectosecond",
    "hour",
    "kilosecond",
    "megasecond",
    "microsecond",
    "millisecond",
    "minute",
    "nanosecond",
    "petasecond",
    "picosecond",
    "second",
    "terasecond",
    "yoctosecond",
    "yottasecond",
    "zeptosecond",
    "zettasecond",
]

AxisType = Literal["batch", "channel", "index", "time", "space"]
ShortId = Annotated[Identifier, MaxLen(16)]
OtherTensorAxisId = Annotated[str, MaxLen(33)]
TensorAxisId = Union[ShortId, OtherTensorAxisId]
SAME_AS_TYPE = "<same as type>"


class ParametrizedSize(Node):
    """Describes a range of valid tensor axis sizes"""

    min: Annotated[int, Gt(0)]
    step: Annotated[int, Gt(0)]
    step_with: Union[TensorAxisId, Literal["BATCH_AXES"], None] = None
    """name of another axis to resize jointly,
    i.e. `n=n_other` for `size = min + n*step`, `size_other = min_other + n_other*step_other`.
    To step with an axis of another tensor, use `step_with = <tensor name>.<axis name>`.
    `step_with="BATCH_AXES"` is a special value to step jointly with all batch dimensions.
    """


class ParametrizedBatchSize(ParametrizedSize):
    """Any batch axis size must be parametrized by `min=1`, `step=1` and `step_with` all batch axes jointly."""

    min: Literal[1] = 1
    step: Literal[1] = 1
    step_with: Literal["BATCH_AXES"] = "BATCH_AXES"


class SizeReference(Node):
    """A tensor axis size defined in relation to another `reference` tensor axis

    `size = reference.size / reference.scale * axis.scale + offset`
    The axis and the referenced axis need to have the same unit (or no unit).
    `scale=1.0`, if the axes have a no scale.
    """

    reference: TensorAxisId
    offset: Annotated[int, Ge(0)] = 0


# this Axis definition is compatible with the NGFF draft from July 10, 2023
# https://ngff.openmicroscopy.org/latest/#axes-md
class AxisBase(Node):
    type: Literal["batch", "channel", "index", "time", "space"]

    name: Union[ShortId, Tuple[ShortId]]
    """a unique name"""

    description: Annotated[str, MaxLen(128)] = ""

    size: Union[int, ParametrizedSize, SizeReference, TensorAxisId]
    """The axis size.
    To specify that this axis' size equals another, an axis name can be given.
    Specify another tensor's axis as `<tensor name>.<axis name>`."""

    @property
    def name_string(self) -> str:
        if isinstance(self.name, str):
            return self.name
        else:
            return ",".join(self.name)


class WithHalo(Node):
    halo: Annotated[int, Ge(0)] = 0
    """The halo should be cropped from the output tensor to avoid boundary effects.
    It is to be cropped from both sides, i.e. `size_after_crop = size - 2 * halo`.
    To document a halo that is already cropped by the model use `size.offset` instead."""


class BatchAxis(AxisBase):
    type: Literal["batch"] = "batch"
    name: ShortId = "batch"
    size: ParametrizedBatchSize = ParametrizedBatchSize()


class ChannelAxis(AxisBase):
    type: Literal["channel"] = "channel"
    name: Tuple[ShortId, ...]


class IndexAxis(AxisBase):
    type: Literal["index"] = "index"
    name: ShortId = "index"


class TimeAxis(AxisBase):
    type: Literal["time"] = "time"
    name: ShortId = "time"
    unit: TimeUnit
    scale: Annotated[float, Gt(0)] = 1.0


class SpaceAxis(AxisBase):
    type: Literal["space"] = "space"
    name: ShortId = Field("x", examples=["x", "y", "z"])
    unit: SpaceUnit
    scale: Annotated[float, Gt(0)] = 1.0


Axis = Annotated[Union[BatchAxis, ChannelAxis, IndexAxis, TimeAxis, SpaceAxis], Field(discriminator="type")]


class OutputTimeAxis(TimeAxis, WithHalo):
    pass


class OutputSpaceAxis(SpaceAxis, WithHalo):
    pass


OutputAxis = Annotated[
    Union[BatchAxis, ChannelAxis, IndexAxis, OutputTimeAxis, OutputSpaceAxis], Field(discriminator="type")
]


class TensorValueBase(Node):
    description: Annotated[str, MaxLen(128)] = ""
    """Brief descripiton of tensor values"""


class NominalTensorValue(TensorValueBase):
    type: Literal["nominal"] = "nominal"
    values: Tuple[Union[int, float, str, bool], ...]


class OrdinalTensorValue(TensorValueBase):
    type: Literal["ordinal"] = "ordinal"
    values: Tuple[Union[int, float, str, bool], ...]
    """values in ascending order"""


class IntervalTensorValueBase(TensorValueBase):
    unit: SiUnit
    factor: float = 1.0
    data_type: Literal["float32", "float64", "uint8", "int8", "uint16", "int16", "uint32", "int32", "uint64", "int64"]
    data_range: Tuple[Optional[float], Optional[float]] = (
        None,
        None,
    )
    """Tuple `(minimum, maximum)` specifying the allowed range of the data in this tensor.
    `None` correspond to min/max of what can be expressed by `data_type`."""


class IntervalTensorValue(IntervalTensorValueBase):
    type: Literal["interval"] = "interval"


class RatioTensorValue(IntervalTensorValueBase):
    type: Literal["ratio"] = "ratio"
    offset: float = 0.0


TensorValue = Annotated[
    Union[NominalTensorValue, OrdinalTensorValue, IntervalTensorValue, RatioTensorValue], Field(discriminator="type")
]


class TensorBase(Node):
    name: Identifier  # todo: validate duplicates
    """Tensor name. No duplicates are allowed."""

    description: Annotated[str, MaxLen(128)] = ""
    """Brief descripiton of the tensor"""

    axes: Tuple[Axis, ...]

    test_tensor: FileSource
    """An example tensor to use for testing.
    Using the model with the test input tensors is expected to yield the test output tensors.
    Each test tensor has be a an ndarray in the
    [numpy.lib file format](https://numpy.org/doc/stable/reference/generated/numpy.lib.format.html#module-numpy.lib.format).
    The file extension must be '.npy'."""

    sample_tensor: Optional[FileSource] = None
    """A sample tensor to illustrate a possible input/output for the model,
    The sample files primarily serve to inform a human user about an example use case
    and are typically stored as HDF5, PNG or TIFF images."""

    values: Union[TensorValue, Tuple[TensorValue, ...]]
    """Description of tensor values, optionally per channel.
    If specified per channel, `data_type` needs to match across channels for interval and ratio type values."""

    @field_validator("axes", mode="after")
    @classmethod
    def validate_axes(cls, axes: Tuple[Axis, ...]):
        seen: Set[str] = set()
        duplicate_axes_names: Set[str] = set()
        for a in axes:
            axis_name = a.name if isinstance(a.name, str) else ",".join(a.name)
            (duplicate_axes_names if axis_name in seen else seen).add(axis_name)

        if duplicate_axes_names:
            raise ValueError(f"Duplicate axis names: {duplicate_axes_names}")

        return axes


class InputTensor(TensorBase):
    preprocessing: Tuple[v0_4.Preprocessing, ...] = ()
    """Description of how this input should be preprocessed."""

    @model_validator(mode="after")
    def validate_preprocessing_kwargs(self):
        axes_names = [a.name for a in self.axes]
        for p in self.preprocessing:
            kwarg_axes = p.kwargs.get("axes", ())
            if any(a not in axes_names for a in kwarg_axes):
                raise ValueError("`kwargs.axes` needs to be subset of axes names")

        return self


class OutputTensor(TensorBase):
    axes: Tuple[OutputAxis, ...]

    postprocessing: Tuple[v0_4.Postprocessing, ...] = ()
    """Description of how this output should be postprocessed."""

    @model_validator(mode="after")
    def validate_postprocessing_kwargs(self):
        axes_names = [a.name for a in self.axes]
        for p in self.postprocessing:
            kwarg_axes = p.kwargs.get("axes", ())
            if any(a not in axes_names for a in kwarg_axes):
                raise ValueError("`kwargs.axes` needs to be subset of axes names")

        return self


class ArchitectureFromSource(Node):
    callable: v0_4.CallableFromSourceFile = Field(examples=["my_function.py:MyNetworkClass"])
    """Callable returning a torch.nn.Module instance.
    `<relative path to file>:<identifier of implementation within the file>`."""

    sha256: Sha256 = Field(
        description="The SHA256 of the architecture source file." + SHA256_HINT,
    )
    """The SHA256 of the callable source file."""

    kwargs: FrozenDictNode[NonEmpty[str], RawLeafValue] = Field(default_factory=dict)
    """key word arguments for the `callable`"""


class ArchitectureFromDependency(Node):
    callable: v0_4.CallableFromDepencency = Field(examples=["my_module.submodule.get_my_model"])
    """callable returning a torch.nn.Module instance.
    `<dependency-package>.<[dependency-module]>.<identifier>`."""

    kwargs: FrozenDictNode[NonEmpty[str], RawLeafValue] = Field(default_factory=dict)
    """key word arguments for the `callable`"""


Architecture = Union[ArchitectureFromSource, ArchitectureFromDependency]


class PytorchStateDictEntry(v0_4.WeightsEntryBase):
    type: Literal["pytorch_state_dict"] = Field("pytorch_state_dict", exclude=True)
    weights_format_name: ClassVar[str] = "Pytorch State Dict"
    architecture: Architecture

    pytorch_version: Annotated[Union[Version, None], warn(Version)] = None
    """Version of the PyTorch library used.
    If `depencencies` is specified it should include pytorch and the verison has to match.
    (`dependencies` overrules `pytorch_version`)"""


WeightsEntry = Annotated[
    Union[
        v0_4.KerasHdf5Entry,
        v0_4.OnnxEntry,
        v0_4.TorchscriptEntry,
        PytorchStateDictEntry,
        v0_4.TensorflowJsEntry,
        v0_4.TensorflowSavedModelBundleEntry,
    ],
    Field(discriminator="type"),
]


class ModelRdf(Node):
    rdf_source: FileSource
    """URL or relative path to a model RDF"""

    sha256: Sha256
    """SHA256 checksum of the model RDF specified under `rdf_source`."""


class Model(
    generic.v0_3.GenericBaseNoSource
):  # todo: do not inherite from v0_4.Model, e.g. 'inputs' are not compatible
    """Specification of the fields used in a bioimage.io-compliant RDF to describe AI models with pretrained weights.

    These fields are typically stored in a YAML file which we call a model resource description file (model RDF).
    Like any RDF, a model RDF can be downloaded from or uploaded to the bioimage.io website and is produced or consumed
    by bioimage.io-compatible consumers (e.g. image analysis software or another website).
    """

    model_config = {
        **generic.v0_3.GenericBaseNoSource.model_config,
        **dict(title="bioimage.io model specification"),
    }
    """pydantic model_config"""

    format_version: Literal["0.5.0"] = "0.5.0"

    type: Literal["model"] = "model"
    """specialized type 'model'"""

    authors: Annotated[Tuple[v0_4.Author, ...], MinLen(1)]
    """The authors are the creators of the model RDF and the primary points of contact."""

    badges: ClassVar[tuple] = ()  # type: ignore
    """Badges are not allowed for model RDFs"""

    documentation: Union[FileSource, None] = Field(
        None,
        examples=[
            "https://raw.githubusercontent.com/bioimage-io/spec-bioimage-io/main/example_specs/models/unet2d_nuclei_broad/README.md",
            "README.md",
        ],
        in_package=True,
    )
    """URL or relative path to a markdown file with additional documentation.
    The recommended documentation file name is `README.md`. An `.md` suffix is mandatory.
    The documentation should include a '[#[#]]# Validation' (sub)section
    with details on how to quantitatively validate the model on unseen data."""

    inputs: Annotated[Tuple[InputTensor, ...], MinLen(1)]
    """Describes the input tensors expected by this model."""

    @field_validator("inputs", mode="after")
    @classmethod
    def validate_input_axes(cls, inputs: Tuple[InputTensor]) -> Tuple[InputTensor]:
        tensor_axes_names = [f"{ipt.name}.{a.name}" for ipt in inputs for a in ipt.axes if not isinstance(a.size, str)]
        for i, ipt in enumerate(inputs):
            valid_axes_references = (
                [None] + [a.name for a in ipt.axes if not isinstance(a.size, str)] + tensor_axes_names
            )
            for a, ax in enumerate(ipt.axes):
                if isinstance(ax.size, ParametrizedSize) and ax.size.step_with not in valid_axes_references:
                    raise ValueError(
                        f"Invalid tensor axis reference at inputs[{i}].axes[{a}].size.step_with: {ax.size.step_with}."
                    )
                if isinstance(ax.size, str) and ax.size not in valid_axes_references:
                    raise ValueError(f"Invalid tensor axis reference at inputs[{i}].axes[{a}].size: {ax.size}.")

        return inputs

    license: LicenseId = Field(examples=["MIT", "CC-BY-4.0", "BSD-2-Clause"])
    """A [SPDX license identifier](https://spdx.org/licenses/).
    We do notsupport custom license beyond the SPDX license list, if you need that please
    [open a GitHub issue](https://github.com/bioimage-io/spec-bioimage-io/issues/new/choose)
    to discuss your intentions with the community."""

    name: Annotated[
        CapitalStr,
        warn(MaxLen(64)),
    ] = Field(pattern=r"\w+[\w\- ]*\w")
    """"A human-readable name of this model.
    It should be no longer than 64 characters
    and may only contain letter, number, underscore, minus or space characters."""

    outputs: Annotated[Tuple[OutputTensor, ...], MinLen(1)]
    """Describes the output tensors."""

    @field_validator("outputs", mode="after")
    @classmethod
    def validate_output_axes(cls, outputs: Tuple[OutputTensor], info: FieldValidationInfo) -> Tuple[OutputTensor]:
        input_tensor_axes_names = [
            f"{ipt.name}.{a.name}"
            for ipt in info.data.get("inputs", ())
            for a in ipt.axes
            if not isinstance(a.size, str)
        ]
        output_tensor_axes_names = [
            f"{out.name}.{a.name}" for out in outputs for a in out.axes if not isinstance(a.size, str)
        ]

        for i, out in enumerate(outputs):
            valid_axes_references = (
                [None]
                + [a.name for a in out.axes if not isinstance(a.size, str)]
                + input_tensor_axes_names
                + output_tensor_axes_names
            )
            for a, ax in enumerate(out.axes):
                if isinstance(ax.size, ParametrizedSize) and ax.size.step_with not in valid_axes_references:
                    raise ValueError(
                        f"Invalid tensor axis reference outputs[{i}].axes[{a}].size.step_with: {ax.size.step_with}."
                    )
                if isinstance(ax.size, str) and ax.size not in valid_axes_references:
                    raise ValueError(f"Invalid tensor axis reference at outputs[{i}].axes[{a}].size: {ax.size}.")

        return outputs

    packaged_by: Tuple[v0_4.Author, ...] = ()
    """The persons that have packaged and uploaded this model.
    Only required if those persons differ from the `authors`."""

    parent: Optional[Union[v0_4.LinkedModel, ModelRdf]] = None
    """The model from which this model is derived, e.g. by fine-tuning the weights."""

    run_mode: Annotated[Optional[v0_4.RunMode], warn(None)] = None
    """Custom run mode for this model: for more complex prediction procedures like test time
    data augmentation that currently cannot be expressed in the specification.
    No standard run modes are defined yet."""

    @classmethod
    def convert_from_older_format(cls, data: RawMapping) -> RawMapping:
        data = super().convert_from_older_format(data)
        fv = data.get("format_version")
        if not isinstance(fv, str) or fv.count(".") != 3:
            return data

        major, minor, _ = map(int, fv.split("."))
        if (major, minor) > (0, 5):
            return data

        if minor == 4:
            data = cls.convert_model_from_v0_4_to_0_5_0(data)

        return data

    @staticmethod
    def _update_v0_4_tensor_specs(
        tensor_specs: List[Union[Any, Dict[str, Any]]],
        test_tensors: Union[Any, List[Any]],
        sample_tensors: Union[Any, List[Any]],
    ) -> None:
        axis_letter_map = {"t": "time", "c": "channel", "i": "index"}

        def convert_axes(tensor_spec: Dict[str, Any]):
            axes = tensor_spec.get("axes")
            if isinstance(axes, str):
                tensor_spec["axes"] = [dict(role=axis_letter_map.get(a, a)) for a in axes]

        for i, param in enumerate(tensor_specs):
            if not isinstance(param, dict):
                continue

            convert_axes(param)
            if isinstance(test_tensors, collections.Sequence) and len(test_tensors) == len(tensor_specs):
                param["test_tensor"] = test_tensors[i]

            if isinstance(sample_tensors, collections.Sequence) and len(sample_tensors) == len(tensor_specs):
                param["sample_tensor"] = sample_tensors[i]

    @classmethod
    def convert_model_from_v0_4_to_0_5_0(cls, data: RawMapping) -> RawMapping:
        # convert axes string to axis descriptions
        data = dict(data)

        inputs = data.get("inputs")
        outputs = data.get("outputs")
        sample_inputs = data.get("sample_inputs")
        sample_outputs = data.get("sample_outputs")
        test_inputs = data.get("test_inputs")
        test_outputs = data.get("test_outputs")

        if isinstance(inputs, collections.Sequence):
            data["inputs"] = list(inputs)
            cls.update_tensor_specs(inputs, test_inputs, sample_inputs)

        if isinstance(outputs, collections.Sequence):
            data["outputs"] = list(outputs)
            cls.update_tensor_specs(outputs, test_outputs, sample_outputs)

        cls._convert_architecture_field(data)

        data["format_version"] = "0.5.0"
        return data

    @staticmethod
    def _convert_architecture_field(data: Dict[str, Any]) -> None:
        weights: "Any | Dict[str, Any]" = data.get("weights")
        if not isinstance(weights, dict):
            return

        state_dict_entry: "Any | Dict[str, Any]" = weights.get("pytorch_state_dict")  # type: ignore
        if not isinstance(state_dict_entry, dict):
            return

        callable_ = state_dict_entry.pop("architecture")  # type: ignore
        sha = state_dict_entry.pop("architecture_sha256")  # type: ignore
        state_dict_entry["architecture"] = dict(callable=callable_, sha256=sha)  # type: ignore
        kwargs = state_dict_entry.pop("kwargs")  # type: ignore
        if kwargs:
            state_dict_entry["architecture"]["kwargs"] = kwargs  # type: ignore
