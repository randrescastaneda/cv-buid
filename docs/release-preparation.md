# Review distribution and release preparation

This is development version 0.2.0.dev0, not a tagged or public package release.
The native CI workflow builds one wheel, includes the MIT license and dependency
notices, records its source commit and SHA256, and installs that exact wheel on
Windows and macOS. Artifacts are private review downloads retained for 14 days.

Extract the review-wheel artifact, keep its files together, and install with:

```sh
python3 -m pip install --no-index --no-deps --require-hashes -r requirements.txt
```

On Windows use `py -3` instead of `python3`. This installs a fixed verified wheel
without resolving runtime dependencies. Quarto, TeX and optional YAML support
remain separately configured dependencies. This is reproducible installation,
not a promise that all future external TeX distributions are byte-identical.

Before any release: review supported Python/platform results, finish user-facing
upgrade/error checks, validate the source distribution, confirm fonts/templates
and license notices, review the generic starter and documentation, and authorize
version/tag/registry publication separately. No workflow publishes a release.
The earlier unversioned local Word-first work remains preserved, not silently
folded into this package. QMD authority and existing private renderers are retained.
