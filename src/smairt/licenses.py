"""Project-license rendering and managed-file ownership checks."""

from __future__ import annotations

import json
from pathlib import Path

from smairt.models import ProjectLicense
from smairt.utils import sha256_text


def render_license(license_name: ProjectLicense, holder: str) -> str | None:
    """Return a clear project license notice, or no file for an undecided project."""
    if license_name is ProjectLicense.UNSPECIFIED:
        return None
    if license_name is ProjectLicense.MIT:
        return f"""MIT License

Copyright (c) {holder}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    if license_name is ProjectLicense.BSD_3_CLAUSE:
        return f"""BSD 3-Clause License

Copyright (c) {holder}
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED. IN NO EVENT SHALL THE
COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES ARISING IN ANY WAY
OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
DAMAGE.
"""
    if license_name is ProjectLicense.APACHE_2_0:
        return f"""Apache License 2.0

Copyright {holder}

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License. You may obtain a copy at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations.
"""
    if license_name is ProjectLicense.GPL_3_0_ONLY:
        return f"""GNU General Public License v3.0 only

Copyright (c) {holder}

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See https://www.gnu.org/licenses/gpl-3.0.html for
the complete license terms.
"""
    return f"""Proprietary

Copyright (c) {holder}. All rights reserved.

No permission is granted to use, copy, modify, distribute, sublicense, or sell
this project without a separate written agreement from the copyright holder.
"""


def license_manifest(license_name: ProjectLicense, content: str) -> str:
    """Serialize the managed license identity and exact expected checksum."""
    return (
        json.dumps(
            {"schema_version": 1, "license": license_name.value, "sha256": sha256_text(content)},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def verify_managed_license(root: Path) -> None:
    """Refuse to replace a license whose managed content was edited by a researcher."""
    manifest_path = root / ".smairt/license.json"
    license_path = root / "LICENSE"
    if not manifest_path.exists():
        if license_path.exists():
            raise ValueError("existing LICENSE is not managed by SMAIRT; review it manually")
        return
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not license_path.exists():
        raise ValueError("managed LICENSE is missing; restore it before changing licenses")
    if sha256_text(license_path.read_text(encoding="utf-8")) != payload.get("sha256"):
        raise ValueError("managed LICENSE was modified; SMAIRT will not overwrite it")
