# Run from the repository root with: make -C docs
# All TeX outputs, auxiliary files, and writable TeX caches stay in docs/.
export TEXMFVAR := $(CURDIR)/.texmf-var
export TEXMFCONFIG := $(CURDIR)/.texmf-config
export TEXMFOUTPUT := $(CURDIR)

.PHONY: all
all: project-guide.pdf

project-guide.pdf: project-guide.tex
	latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=. $<
