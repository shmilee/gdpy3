# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXAPIDOC  = sphinx-apidoc
SPHINXPROJ    = gdpy3
SOURCEDIR     = source
BUILDDIR      = build
PROJPATH      = $(shell python -c "import gdpy3; print(gdpy3.__path__[0])")

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

srcrst:
	@mkdir -pv "$(SOURCEDIR)"/_static "$(SOURCEDIR)"/_templates
	@echo 'MODULE_PATH is' $(PROJPATH)
	@$(SPHINXAPIDOC) -M -f -o "$(SOURCEDIR)" "$(PROJPATH)" $(SPHINXOPTS) $(O)

cleanrst:
	@rm -rf "$(SOURCEDIR)/$(SPHINXPROJ)"*.rst

clean:
	@rm -rf "$(BUILDDIR)"

.PHONY: help Makefile cleanrst clean

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
