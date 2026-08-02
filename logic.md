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

REMEMBER
before converting the sample into the template for the compiler, remove all the things that should be set by defaults