# Third-Party Notices

Ontime Cue Sheet is licensed under the Zero-Clause BSD license (`0BSD`). The following third-party components are not covered by the project's 0BSD license and remain subject to their own license terms.

## Direct runtime dependencies

| Component | License | Project |
| --- | --- | --- |
| FastAPI | MIT | <https://github.com/fastapi/fastapi> |
| HTTPX | BSD 3-Clause | <https://github.com/encode/httpx> |
| Jinja | BSD 3-Clause | <https://github.com/pallets/jinja> |
| python-multipart | Apache License 2.0 | <https://github.com/Kludex/python-multipart> |
| Uvicorn | BSD 3-Clause | <https://github.com/encode/uvicorn> |
| WeasyPrint | BSD 3-Clause | <https://github.com/Kozea/WeasyPrint> |

## PDF rendering components

WeasyPrint uses additional Python and native rendering dependencies. The project's container builds install Pango from Debian packages. These components remain under their own licenses; installed distributions and container packages include their applicable copyright and license information.

- WeasyPrint dependency information: <https://doc.courtbouillon.org/weasyprint/stable/first_steps.html>
- Pango source and licensing: <https://gitlab.gnome.org/GNOME/pango>
- Python container image licensing: <https://hub.docker.com/_/python>

## WeasyPrint license

BSD 3-Clause License

Copyright (c) 2011-2021, Simon Sapin and contributors.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
