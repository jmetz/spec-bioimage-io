from __future__ import annotations

import shutil
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterator, Optional, Tuple, Type, get_args

from pydantic.alias_generators import to_pascal, to_snake
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from bioimageio.spec import ResourceDescription, application, collection, dataset, generic, model, notebook
from bioimageio.spec.shared.nodes import Node

Loc = Tuple[str, ...]

ANNOTATION_MAP = {
    "pydantic_core._pydantic_core.Url": "Url",
    "typing.": "",
    "bioimageio.spec.shared.nodes.FrozenDictNode": "Dict",
    "bioimageio.spec.shared.types.": "",
    "bioimageio.spec.": "",
    "NoneType": "None",
    "Ellipsis": "...",
}
MAX_LINE_WIDTH = 120


def get_subnodes(loc: Loc, annotation: Any) -> Iterator[Tuple[Loc, Type[Node]]]:
    try:
        is_node = issubclass(annotation, Node)
    except TypeError:
        is_node = False

    if is_node:
        yield loc, annotation
    else:
        for like_list in ["List", "Tuple", "Set"]:
            if str(annotation).startswith(f"typing.{like_list}["):
                loc = loc[:-1] + (loc[-1] + ".i",)
                break

        for sa in get_args(annotation):
            yield from get_subnodes(loc, sa)


@dataclass
class AnnotationName:
    annotation: Any
    indent_level: int
    footnotes: OrderedDict[str, str]
    full_maybe_multiline: str = field(init=False)
    full_inline: str = field(init=False)
    abbreviated: Optional[str] = field(init=False)
    kind: str = field(init=False)

    annotation_map: Dict[str, str]

    def __post_init__(self):
        self.full_maybe_multiline = self.get_name(self.annotation, abbreviate=False, inline=False)
        self.full_inline = self.get_name(self.annotation, abbreviate=False)
        self.kind = self._get_kind()
        if self.indent_level + len(self.full_inline) > MAX_LINE_WIDTH:
            self.abbreviated = self.get_name(self.annotation, abbreviate=True)
        else:
            self.abbreviated = None

    def _get_kind(self):
        s = self.full_inline
        brackets = 0
        max_balance = -1
        for i in range(min(len(s), 32)):
            if s[i] == "[":
                brackets += 1

            if s[i] == "]":
                brackets -= 1

            if brackets == 0:
                max_balance = i

        return s[: max_balance + 1]

    def slim(self, s: str):
        """shortening that's always OK"""
        s = s.strip("'\"")
        if s.startswith("<class ") and s.endswith(">"):
            s = s[len("<class ") : -1]

        s = s.strip("'\"")
        for k, v in self.annotation_map.items():
            if s.startswith(k):
                s = v + s[len(k) :]
                break

        return s.strip("'\"")

    def more_common_name(self, type_name: str):
        bracket = type_name.find("[")
        if bracket == -1:
            first_part = type_name
        else:
            first_part = type_name[:bracket]

        common_name = {"List": "Sequence", "Tuple": "Sequence"}.get(first_part, first_part)
        if bracket == -1:
            return common_name
        else:
            return common_name + type_name[bracket:]

    def get_name(self, t: Any, abbreviate: bool, inline: bool = True, multiline_level: int = 0) -> str:
        if isinstance(t, FieldInfo):
            parts = list(t.metadata)
            if t.discriminator:
                parts.append(f"discriminator={t.discriminator}")

            return "; ".join(parts)

        s = self.slim(str(t))
        if s.startswith("Annotated["):
            args = get_args(t)
            if abbreviate:
                return f"{self.get_name(args[0], abbreviate, inline, multiline_level)}*"

            annotated_type = self.get_name(args[0], abbreviate, inline, multiline_level)
            annos = f"({'; '.join([self.get_name(tt, abbreviate, inline, multiline_level) for tt in args[1:]])})"
            if inline or abbreviate or (multiline_level + len(annotated_type) + 1 + len(annos) < MAX_LINE_WIDTH):
                anno_sep = " "
            else:
                anno_sep = "\n" + " " * multiline_level * 2

            return f"{annotated_type}{anno_sep}{annos}"

        if s.startswith("Optional["):
            return f"Optional[{self.get_name(get_args(t)[0], abbreviate, inline, multiline_level)}]"

        for format_like_list in ["Union", "Tuple", "Literal", "Dict", "List", "Set"]:
            if not s.startswith(format_like_list):
                continue

            args = get_args(t)
            if format_like_list == "Tuple" and len(args) == 2 and args[1] == ...:
                args = args[:1]

            format_like_list_name = self.more_common_name(format_like_list)

            if len(args) > 4 and abbreviate:
                args = [args[0], "...", args[-1]]

            parts = [self.get_name(tt, abbreviate, inline, multiline_level) for tt in args]
            one_line = f"{format_like_list_name}[{', '.join(parts)}]"
            if abbreviate or inline or (self.indent_level + len(one_line) < MAX_LINE_WIDTH):
                return one_line

            first_line_descr = f"{format_like_list_name} of"
            if len(args) == 1:
                more_maybe_multiline = self.get_name(
                    args[0], abbreviate=abbreviate, inline=inline, multiline_level=multiline_level
                )
                return first_line_descr + " " + more_maybe_multiline

            parts = [self.get_name(tt, abbreviate, inline=inline, multiline_level=multiline_level + 1) for tt in args]
            multiline_parts = f"\n{' '* multiline_level * 2}- ".join(parts)
            return f"{first_line_descr}\n{' '* multiline_level * 2}- {multiline_parts}\n"

        return s


class Field:
    STYLE_SWITCH_DEPTH = 4

    def __init__(
        self, loc: Loc, info: FieldInfo, *, footnotes: OrderedDict[str, str], rd_class: type[ResourceDescription]
    ) -> None:
        assert loc
        self.loc = loc
        self.info = info
        self.footnotes = footnotes
        self.annotation_map = {f"{rd_class.__module__}.": "", **ANNOTATION_MAP}
        self.rd_class = rd_class

    @property
    def indent_with_symbol(self):
        spaces = " " * max(0, self.indent_level - 2)
        if len(self.loc) <= self.STYLE_SWITCH_DEPTH:
            symbol = f"#{'#'* len(self.loc)} "
        else:
            symbol = "* "

        return f"{spaces}{symbol}"

    @property
    def indent_level(self):
        return max(0, len(self.loc) - self.STYLE_SWITCH_DEPTH) * 2

    @property
    def indent_spaces(self):
        return " " * self.indent_level

    @property
    def name(self):
        n = ".".join(self.loc)
        if len(self.loc) <= self.STYLE_SWITCH_DEPTH:
            return f"`{n}`"
        else:
            return f'<a id="{n}"></a>`{n}`'

    @property
    def title(self):
        return self.info.title or ""

    @property
    def description(self):
        return unindent(self.info.description or "")

    @property
    def explanation(self):
        ret = self.indent_spaces
        if self.info.title:
            ret += f"{self.title}: "
            if "\n" in self.description or len(ret) + len(self.description) > MAX_LINE_WIDTH:
                ret += "\n"

        ret += self.description

        return ret.replace("\n", self.indent_spaces + "\n")

    @property
    def default(self):
        if self.info.default is PydanticUndefined:
            return ""
        else:
            d = self.info.get_default(call_default_factory=True)
            if d == "":
                d = r"\<empty string\>"

            return f" = {d}"

    @property
    def md(self) -> str:
        nested = ""
        for subloc, subnode in get_subnodes(self.loc, self.info.annotation):
            sub_anno = AnnotationName(
                annotation=subnode,
                footnotes=self.footnotes,
                indent_level=self.indent_level + 2,
                annotation_map=self.annotation_map,
            ).full_inline
            subfields = ""
            for sfn, sinfo in subnode.model_fields.items():
                subfields += "\n" + Field(subloc + (sfn,), sinfo, footnotes=self.footnotes, rd_class=self.rd_class).md
            if subfields:
                nested += "\n" + self.indent_spaces + sub_anno + ":" + subfields

        an = AnnotationName(
            annotation=self.info.annotation,
            footnotes=self.footnotes,
            indent_level=self.indent_level,
            annotation_map=self.annotation_map,
        )
        first_line = f"{self.indent_with_symbol}{self.name}<sub> {an.kind}</sub>{self.default}\n"
        if (nested or an.abbreviated) and len(self.loc) <= self.STYLE_SWITCH_DEPTH:
            if an.kind == an.full_inline:
                expaned_type_anno = ""
            else:
                expaned_type_anno = an.full_maybe_multiline + "\n"

            ret = (
                f"{first_line}{self.explanation}\n"
                f"<details><summary>{an.abbreviated or an.full_inline}\n\n</summary>\n\n"
                f"{expaned_type_anno}{nested}\n</details>\n"
            )
        else:
            ret = f"{first_line}{self.explanation}\n{'' if an.kind == an.full_inline else an.full_inline}{nested}\n"

        return ret


def get_documentation_file_name(rd_class: Type[ResourceDescription], *, latest: bool = False):
    typ = to_snake(rd_class.__name__)
    if latest:
        v = "latest"
    else:
        v = f"v{rd_class.implemented_format_version.replace('.', '-')}"

    return f"{typ}_{v}.md"


def unindent(text: str, ignore_first_line: bool = True):
    """remove minimum count of spaces at beginning of each line.

    Args:
        text: indented text
        ignore_first_line: allows to correctly unindent doc strings
    """
    first = int(ignore_first_line)
    lines = text.split("\n")
    filled_lines = [line for line in lines[first:] if line]
    if len(filled_lines) < 2:
        return "\n".join(line.strip() for line in lines)

    indent = min(len(line) - len(line.lstrip(" ")) for line in filled_lines)
    return "\n".join(lines[:first] + [line[indent:] for line in lines[first:]])


def export_documentation(folder: Path, rd_class: Type[ResourceDescription]) -> Path:
    footnotes: OrderedDict[str, str] = OrderedDict()
    md = "# " + (rd_class.model_config.get("title") or "") + "\n" + (unindent(rd_class.__doc__ or ""))
    field_names = ["type", "format_version"] + [
        fn for fn in rd_class.model_fields if fn not in ("type", "format_version")
    ]
    for field_name in field_names:
        info = rd_class.model_fields[field_name]
        md += "\n" + Field((field_name,), info, footnotes=footnotes, rd_class=rd_class).md

    md += "\n"
    for i, full in enumerate(footnotes, start=1):
        md += f"\n[^{i}]: {full}"

    file_path = folder / get_documentation_file_name(rd_class)
    file_path.write_text(md, encoding="utf-8")
    print(f"written {file_path}")
    return file_path


def export_module_documentations(folder: Path, module: ModuleType):
    rd_name = to_pascal(module.__name__.split(".")[-1])

    rd_class = None
    latest = None
    v = None
    for v in sorted(dir(module)):
        v_module = getattr(module, v)
        if not hasattr(v_module, rd_name):
            continue

        rd_class = getattr(v_module, rd_name)
        latest = export_documentation(folder, rd_class)

    assert latest is not None
    assert rd_class is not None
    shutil.copy(str(latest), folder / get_documentation_file_name(rd_class, latest=True))
    print(f" copied {latest} as latest")


if __name__ == "__main__":
    dist = (Path(__file__).parent / "../dist").resolve()
    dist.mkdir(exist_ok=True)

    export_module_documentations(dist, application)
    export_module_documentations(dist, collection)
    export_module_documentations(dist, dataset)
    export_module_documentations(dist, generic)
    export_module_documentations(dist, model)
    export_module_documentations(dist, notebook)
