# SEGREG – segregation of conditioned stimuli in the nucleus interpositus

Interactive simulation accompanying the article:

> Beunis R. (2021). An Eye Blink Reflex Model based on an Intracellular Timing Mechanism in Purkinje Cells and on a Conditioned Stimulus Segregation Mechanism in the Nucleus Interpositus might explain the Double Peaks Phenomenon. Zenodo. https://doi.org/10.5281/zenodo.17584844

The program shows how two conditioned stimuli (CS1, a "tone" followed by the unconditioned stimulus after 800 ms, and CS2, a "light" followed after 400 ms) that compete for the same nanoloops in the nucleus interpositus segregate onto different nanoloops. Mossy fiber (MF) synapses onto nucleo-olivary neurons (NONs) are strengthened by LTP and weakened by LTD. While both CSs still share the nanoloops, each CS also triggers the conditioned response (CR) of the other: the transient "double peaks phenomenon". The demos also show what transfer training does, and how a "metabolic brake" and a little background noise protect an established CS. Every run takes a different random course.


## Live program

https://rob-beunis.github.io/segreg/

It runs in any modern web browser, with nothing to install. Each demo can be opened directly (page numbers are those printed at the bottom of the pages of the article):

- Demo 1 – Components of the demo (Fig. 1, p. 14):
  https://rob-beunis.github.io/segreg/?demo=1
- Demo 2 – Thickening lines (Fig. 2, p. 15):
  https://rob-beunis.github.io/segreg/?demo=2
- Demo 3 – CR curves, double peaks (Fig. 3, p. 15):
  https://rob-beunis.github.io/segreg/?demo=3
- Demo 4 – Complete segregation run (Figs. 4 and 5, p. 16):
  https://rob-beunis.github.io/segreg/?demo=4
- Demo 5 – Traces, random factor on (Fig. 6, p. 18):
  https://rob-beunis.github.io/segreg/?demo=5
- Demo 6 – Traces, random factor off (Fig. 6, p. 18):
  https://rob-beunis.github.io/segreg/?demo=6
- Demo 7 – Transfer training CS1 > CS2 > CS1, metabolic brake off (Fig. 7, p. 19):
  https://rob-beunis.github.io/segreg/?demo=7
- Demo 8 – Transfer training CS1 > CS2, metabolic brake on (Fig. 8a, p. 20):
  https://rob-beunis.github.io/segreg/?demo=8
- Demo 9 – Intermixed, metabolic brake on (Figs. 8b and 8c, p. 20):
  https://rob-beunis.github.io/segreg/?demo=9
- Demo 10 – Erosion of CS1 in a longer run (text, p. 20, no figure):
  https://rob-beunis.github.io/segreg/?demo=10
- Demo 11 – With background noise (text, p. 20, no figure):
  https://rob-beunis.github.io/segreg/?demo=11
- Demo 12 – Interactive mode, all controls (the mode in which the screenshots were taken):
  https://rob-beunis.github.io/segreg/?demo=12

Optional additions to the address:

- `&speed=0.5` plays back at half speed. Values from 0.25 to 16 are accepted. At 1x the program runs at the speed of the original in Visual FoxPro 9 (about 170 steps per second with 20 NONs).
- `&seed=123` gives a reproducible run.

The playback speed can also be changed with the buttons below the demo panel.

The page counts anonymous visits and demo starts with GoatCounter (no cookies, no personal data).

Every button has an explanation (tooltip). With a mouse, rest the pointer on the button; on a tablet or phone, press and hold the button for about half a second. The program is easiest to use in landscape orientation on small screens.


## Contents of this repository

- `index.html`
  The web version (JavaScript, a single self-contained file). This is the live program.

- `python/segreg.py` (with `python/START_SEGREG.bat`)
  The Python/Tkinter version. It requires Python 3 and Pillow (`pip install pillow`).
  Start it with `python segreg.py`, or with options: `--demo N`, `--speed 0.5`, `--seed N`.

- `vfp/segreg.prg`
  The original Visual FoxPro 9.0 program (2020–2021), with its comments translated into English. The code itself is unchanged.

- `vfp/segreg_original_dutch_comments.prg`
  The same program with its original Dutch comments.

The Python and web versions follow `segreg.prg` procedure by procedure, with the same procedure names, rules and parameters, and the same screen layout as the screenshots in the article. They were checked against runs of the original in Visual FoxPro 9. They differ from it in a few deliberate ways:

- Article version: the screenshots and videos of the article were made with the SEGREG form built into the author's article reader. Its visible details are followed: the switch is called "BEAM" (as in the article) instead of "BACKGROUND", the STOP button is always shown, the form width is fixed at 1264 pixels, and each demo shows the same controls.
- Random numbers: the random number generator differs from VFP's `RAND()`, so an individual VFP run cannot be reproduced exactly.
- Speed: 1x is the speed measured in VFP 9. Above 1x, the Python version is limited by the speed of the computer (about 2x).
- Parameters: the parameter table `SEGREGMEM.DBF` is not kept between sessions; the program starts with the demo values.
- Form width: when the trace needs more room, the form widens to the right (in VFP its left edge moved to the left).
- Additions: a demo panel and a playback speed control were added.
- Demos 13 and 14 (compound training, not used in the article) remain in the code, but, as in the article version of the program, the Demo setting only goes up to 11.


## Acknowledgement

The original program was written by the author in Visual FoxPro 9.0. The translations into Python and into the web version were made with the assistance of Claude (Anthropic), an AI assistant, under the direction of the author, and were checked against the original program.


## Author

Rob Beunis, independent researcher (retired clinical neuropsychiatrist), Antwerp, Belgium.
