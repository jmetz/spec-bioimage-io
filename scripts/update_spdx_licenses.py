"""script that updates content of `_license_file` and generates the `LicenseId` Literal"""

import json
from pathlib import Path
import sys
from argparse import ArgumentParser

import urllib.request
import black.files
import black.mode

from bioimageio.spec.shared import _license_file  # type: ignore

ROOT_PATH = Path(__file__).parent.parent

URL = "https://raw.githubusercontent.com/spdx/license-list-data/{tag}/json/licenses.json"
LICENSE_ID_MODULE_PATH = ROOT_PATH / "bioimageio/spec/shared/_generated_spdx_license_type.py"
LICENSE_ID_MODULE_TEMPLATE = """# This file was generated by scripts/update_spdx_licenses.py
from typing import Literal

LicenseId = Literal{license_ids}

DeprecatedLicenseId = Literal{deprecated_license_ids}
"""


def parse_args():
    p = ArgumentParser(description=("script that generates weights formats overview"))
    _ = p.add_argument("tag", nargs="?", default="v3.21")

    args = p.parse_args()
    return dict(tag=args.tag)


def main(*, tag: str):
    text = urllib.request.urlopen(URL.format(tag=tag)).read().decode("utf-8")
    _license_file.write_text(text, encoding="utf-8")
    print(f"Updated {_license_file}")

    licenses = json.loads(text)["licenses"]
    license_ids = [x["licenseId"] for x in licenses if not x["isDeprecatedLicenseId"]]
    deprecated_license_ids = [x["licenseId"] for x in licenses if x["isDeprecatedLicenseId"]]
    code = LICENSE_ID_MODULE_TEMPLATE.format(license_ids=license_ids, deprecated_license_ids=deprecated_license_ids)

    # apply black formating
    black_config = black.files.parse_pyproject_toml(str(ROOT_PATH / "pyproject.toml"))
    black_config["target_versions"] = set(
        (getattr(black.mode.TargetVersion, tv.upper()) for tv in black_config.pop("target_version"))
    )
    code = black.format_str(code, mode=black.mode.Mode(**black_config))

    _ = LICENSE_ID_MODULE_PATH.write_text(code, encoding="utf-8")
    print(f"Updated {LICENSE_ID_MODULE_PATH}")


if __name__ == "__main__":
    kwargs = parse_args()
    sys.exit(main(**kwargs))
