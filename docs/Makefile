# Minimal makefile for Sphinx documentation

SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = ..
BUILDDIR      = _build
CONFDIR       = .

.PHONY: help clean html

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  html     Build HTML documentation"
	@echo "  clean    Remove build artifacts"

html:
	@$(SPHINXBUILD) -b html -c "$(CONFDIR)" "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS)
	@echo "Build finished. Output in $(BUILDDIR)/html/"

clean:
	rm -rf $(BUILDDIR)
