# woas

_"it's just Words On A Screen."_

a domain-specific language used to make text-based games that outputs entirely in HTML5.

## uhh what did you even make?
i built:
- woas language syntax: a semi-easy-to-use language to write text-based games in
- woas compiler: a python script that turns `.woas` files into completely standalone HTML5 files
- woas runtime engine: the javascript game loop inside every woas html file, that turns woas commands into DOM generation, audio playback, and complex storyline managemment

## ts kinda useless, why did you build it?
i made it cause i ~~needed hours for horizons polaris~~ wanted an easy to use engine to make story games/slideshows that are a bit more barebones than what renpy has to offer. i wanted to create a story-based game but the idea of having to use renpy and deal with all of the stuff to make it look nice (UI, character sprites, animations) and not like the default template overwhelmed me. woas is much more barebones and lets your story stand on its own two legs rather than bombarding you with tons of features you might not need that end up looking generic in the end.

## quick start
1. create a plaintext file with the `.woas` file extension
2. write your game in woas using the syntax guide below
3. run the compiler script
4. pass the path to your .woas file

## demo game
i made a game in woas as a demo of the engine!
[more details here once i actually make the game]

## syntax guide
woas is read line-by-line, meaning each line is one command.
woas completely ignores all newlines, so they are optional but usable if you want to make your `.woas` code more readable.
here are the commands you can use:

### 1. game title
sets the name of the tab in the web browser.

note: you can only set one game title - the title command written last will be the one used.
```text
title "My Awesome Game"
```

### 2. displaying text
you can display up to one piece of text on the screen at any moment (not counting choice screens).
text must be wrapped in double quotes (escaped quotes like `\"` inside these quotes are supported). you can optionally add css classes to style this text, and specify a custom color and font after the `/` separator.

- format: "Text" classes / color font
- use `null` in the font slot to use default color but still define a font.

```text
"You wake up in a dark room." s center vcenter
"A loud noise startles you!" xl center / red
"A ghostly whisper..." m right / null "Times New Roman"
```

### 3. choices and branching
ask a question and display choices for the user. when the player clicks a choice linked to a jump marked by an id, the engine will skip to the next "jump [id]" command. the engine avoids hitting the other branches by skipping over jumps (by going to their end command) that aren't triggered specifically by a user-made choice.

format:
- a jump command declaring the jump and its id (which cannot have spaces)
- any commands that should (and will) only be executed if a choice is picked that points to this jump
- an end command declaring the end of the jump, with its id (to clarify which jump is being ended)

engine logic is as follows:
- get to jump -> skip to end command
- if user triggers a choice, skip to the corresponding jump command and execute the commands inside of it

note: choices in a choice command can only jump to jumps declared after the choice command itself.

```text
choice "Which path do you take?" / "Go left" path_left "Go right" path_right / royalblue

jump path_left
"You went left and found a treasure!" m center vcenter / gold
choice "What do you do with your treasure?" / "Sell it" sell "Go back and go right" path_right / gold

jump sell
"You sold it for a lot of money, and now you're rich." m center vcenter
end sell

end path_left

jump path_right
"You went right and fell in a pit." m center vcenter / brown
end path_right
```

### invisible commands
commands below run without stopping the queue, meaning they don't need an input to go to the next command.

### 4. background
change the background to a color or image.
works similarly to the css shorthand property "background".

```text
bg black
bg #a58dca
bg rgb(255, 255, 255)
bg my_image.png
```

### 5. global styling
set the default font and colors, so you don't have to define them for every single text command.
note: these aren't one time for the entire project; you can change these as you go. a usecase for this may be: you enter a new environment that will have a new default font color and font.

```text
color white
font "Courier New"
```

### 6. music
play/resume, pause, or stop a single looping audio track. this feature is designed for background music, so only one track can play at a time, and it will loop infinitely.
note: audio files must be in the same folder as your compiled `.html` file, or linked by url.

```text
music play scary_ambience.mp3
music pause
music stop
```

## contributing
pull requests open! if you have questions about contributing, you can message me on the [Hack Club](https://hackclub.com/) [Slack](https://slack.hackclub.com/) @stellenium, and you can reach me at the email listed on my GitHub README.