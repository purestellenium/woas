this is where i'll note down my plan for the logic flow of the compiler

1. set default stylings, for now just font, font color + imports for custom fonts etc
2. load commands from .woas into a queue managed by html file in JS

commands:
- show text
  - text itself in quotes
  - classes (attributes like size, location) separated by spaces
  - special attributes (font color, font family, margin) which are too tedious to set by 
- set bg
- start playing music
- stop playing music
- show persistent text on the screen
- remove persistent text

SYNTAX IN HTML

text:
["text", "text here", "class list here", "color - set null if none", "font-family - set null if none"]

--- commands below move on to next command after running, not waiting for input ----

background:
["bg", "color or url(path)"]

music (NOTE THAT THIS WONT WORK AS THE FIRST INPUT):
["music", "play", "path"]
or
["music", "stop"]
or
["music", "pause"]

jumps:
["jump", "jumpid"]

skip (jumps straight to a "jump", same as clicking a choice that points there):
["skip", "jumpid"]

SYNTAX IN WOAS

text:
"text here" class list here / color(null if none) font-family(null if none)

background:
bg pathtofile.jpg OR color

music:
music play pathtofile.mp3
or
music stop
or
music pause

choice:
choice "choice question here" / "option 1" jump1 "option 2" jump2 "option 3" jump3 / color

jumps:
jump jumpid

when a jump ends:
end jumpid

skip straight to a jump, without needing a choice to trigger it:
skip jumpid

font (set default font-family):
font font-family

color (set default font color):
color color

import (load a custom font file, usable anywhere a font is accepted):
import "font name" pathtofile.woff2

import (link a font stylesheet like google fonts instead - no name, since the stylesheet already names its own fonts):
import https://fonts.googleapis.com/css2?family=Roboto&display=swap

SYNTAX IN HTML

import (font file only - stylesheet imports become a <link> in <head> instead):
["import", "font name", "pathtofile.woff2"]