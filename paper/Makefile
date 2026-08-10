# Paper build.
#
#   make paper    regenerate figures from ../results, then compile main.pdf
#   make figures  regenerate figures and generated/macros.tex only
#   make watch    continuous rebuild while drafting
#   make clean    remove build intermediates (keeps main.pdf)
#   make distclean  also remove main.pdf and generated/
#
# The point of the figures dependency is that the PDF cannot drift from the
# data. Figures and every reported number are generated artifacts; editing
# them by hand is a defect, not a shortcut.
#
# Requires latexmk and a TeX distribution. `uv` is invoked as `python -m uv`
# because a pip-installed uv does not land on PATH on Windows.

UV      := python -m uv
LATEXMK := latexmk -pdf -interaction=nonstopmode -halt-on-error

.PHONY: paper figures watch clean distclean

paper: figures
	$(LATEXMK) main.tex

# `de figures` reads ../results/**/summary.json and writes figures/*.pdf plus
# generated/macros.tex. With no results present it emits an empty macro file
# and returns cleanly, so the skeleton compiles before any run has happened.
figures:
	cd .. && $(UV) run de figures --out paper

watch: figures
	$(LATEXMK) -pvc main.tex

clean:
	latexmk -c main.tex
	rm -f main.bbl main.run.xml

distclean: clean
	latexmk -C main.tex
	rm -rf generated figures
