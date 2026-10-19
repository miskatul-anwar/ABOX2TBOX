# Project documentation

Read [project-guide.pdf](project-guide.pdf). Its editable source is
[project-guide.tex](project-guide.tex).

Rebuild from the repository root:

```sh
make -C docs
```

The build runs inside `docs/`. The PDF and all LaTeX auxiliary files (`.aux`,
`.log`, `.toc`, `.out`, `.fls`, and `.fdb_latexmk`) remain here. Any writable TeX
configuration or font caches are directed to `.texmf-config/` and `.texmf-var/`
inside this directory. The build deliberately retains its residual files.

The guide describes implementation commit `7a98c41`, explains the current
single-model design, and distinguishes implemented behavior, measured checks,
engineering judgments, and proposed extensions. External references are linked
in the PDF. Application code and datasets are not modified by this documentation
build.
