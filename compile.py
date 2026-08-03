import re, json, os, sys

file_path = sys.argv[1].strip() if len(sys.argv) > 1 else input("Path to .woas file: ").strip()

FONT_FILE_PATTERN = re.compile(r'\.(woff2?|ttf|otf|eot)(?:\?.*)?$', re.I)

def format_error(line_number, source, reason):
    return f"{reason} (line {line_number}): {source.strip()}"

def raise_syntax_error(line_number, line, reason):
    raise SyntaxError(format_error(line_number, line, reason))

def parse_text_line(line, line_number):
    text_match = re.match(r'^"((?:\\.|[^"\\])*)"\s*(.*)$', line.strip())

    if not text_match:
        raise_syntax_error(line_number, line, 'Text line is missing its closing quote, or does not start with "text here"')

    text = text_match.group(1).replace('\\"', '"')
    remainder = text_match.group(2)

    classes = ""
    color = None
    font_family = None

    if '/' in remainder:
        classes_part, rest = remainder.split('/', 1)
        classes = classes_part.strip()
        rest = rest.strip()

        if rest:
            color_font_match = re.match(r'^(\w+\([^)]*\)|\S+)(?:\s+(.*))?$', rest)
            color = color_font_match.group(1)
            font_family = color_font_match.group(2)
    else:
        classes = remainder.strip()

    if color is None or color.lower() == "null":
        color = None

    if font_family is None or font_family.lower() == "null":
        font_family = None
    else:
        quoted_font = re.match(r'^"((?:\\.|[^"\\])*)"$', font_family)
        if quoted_font:
            font_family = quoted_font.group(1).replace('\\"', '"')

    return {
        "text": text,
        "classes": classes,
        "color": color,
        "font_family": font_family
    }

def parse_choice_line(line, line_number):
    main_pattern = r'^choice\s+"((?:\\.|[^"\\])*)"\s*/\s*(.*)$'
    main_match = re.match(main_pattern, line.strip())

    if not main_match:
        raise_syntax_error(line_number, line, 'Choice line does not match \'choice "prompt" / "option text" jump_id ... / color\'')

    prompt = main_match.group(1).replace('\\"', '"')
    rest_of_line = main_match.group(2)
    
    option_pattern = r'"((?:\\.|[^"\\])*)"\s+(\S+)'
    parsed_options = []
    
    last_end = 0 
    
    for match in re.finditer(option_pattern, rest_of_line):
        parsed_options.append({
            "text": match.group(1).replace('\\"', '"'),
            "jump": match.group(2)
        })
        last_end = match.end()
        
    remainder = rest_of_line[last_end:].strip()
    color = None
    
    if remainder.startswith('/'):
        color_string = remainder[1:].strip()
        if color_string and color_string.lower() != "null":
            color = color_string
            
    return {
        "prompt": prompt,
        "options": parsed_options,
        "color": color
    }

def parse_import_line(line, line_number):
    named_match = re.match(r'^import\s+"((?:\\.|[^"\\])*)"\s+(.+)$', line.strip())

    if named_match:
        font_name = named_match.group(1).replace('\\"', '"')
        font_path = named_match.group(2).strip()
    else:
        bare_match = re.match(r'^import\s+(\S+)\s*$', line.strip())
        if not bare_match:
            raise_syntax_error(line_number, line, 'Import line does not match \'import "Font Name" path/to/font.woff2\' or \'import https://stylesheet-url\'')
        font_name = None
        font_path = bare_match.group(1)

    if font_path.startswith('url(') and font_path.endswith(')'):
        font_path = font_path[4:-1].strip('"\'')

    return {
        "name": font_name,
        "path": font_path
    }

def validate_jumps(queue, queue_lines, queue_source):
    jump_positions = {}
    end_positions = {}

    for index, entry in enumerate(queue):
        if entry[0] == "jump":
            jump_positions.setdefault(entry[1], index)
        elif entry[0] == "end":
            end_positions.setdefault(entry[1], index)

    for jump_id, jump_index in jump_positions.items():
        end_index = end_positions.get(jump_id)
        if end_index is None or end_index <= jump_index:
            raise SyntaxError(format_error(
                queue_lines[jump_index],
                queue_source[jump_index],
                f'Invalid jump: "jump {jump_id}" has no matching "end {jump_id}" declared after it'
            ))

    def check_target(index, jump_id, description):
        jump_index = jump_positions.get(jump_id)
        if jump_index is None or jump_index <= index:
            raise SyntaxError(format_error(
                queue_lines[index],
                queue_source[index],
                f'Invalid jump: {description} points to jump "{jump_id}", but no "jump {jump_id}" is declared after this line'
            ))

    for index, entry in enumerate(queue):
        if entry[0] == "choice":
            for option in entry[2]:
                check_target(index, option["jump"], f'choice option "{option["text"]}"')
        elif entry[0] == "skip":
            check_target(index, entry[1], f'"skip {entry[1]}"')

def compile_game_from_file(filepath):
    try:
        title = None
        stylesheets = []

        with open(filepath, 'r') as file:
            queue = []
            queue_lines = []
            queue_source = []

            for line_number, line in enumerate(file, start=1):
                if not line.strip():
                    continue

                if line[0] == '"':
                    data = parse_text_line(line.strip(), line_number)
                    queue.append([
                        "text",
                        data["text"],
                        data["classes"],
                        data["color"],
                        data["font_family"]
                    ])
                elif line.startswith('choice '):
                    data = parse_choice_line(line, line_number)
                    queue.append([
                        "choice",
                        data["prompt"],
                        data["options"],
                        data["color"]
                    ])
                elif line.startswith('title '):
                    match = re.match(r'^title\s+"((?:\\.|[^"\\])*)"', line.strip())
                    if match:
                        title = match.group(1).replace('\\"', '"')
                    continue
                elif line.startswith('bg '):
                    bg_val = line[3:].strip()
                    if re.search(r'\.(png|jpg|jpeg|gif|webp|svg|bmp|avif)$', bg_val, re.I) and not bg_val.startswith('url('):
                        bg_val = f"url('{bg_val}')"
                    queue.append(["bg", bg_val])
                elif line.startswith('font '):
                    match = re.match(r'^font\s+(?:"((?:\\.|[^"\\])*)"|(.+))', line.strip())
                    if not match:
                        raise_syntax_error(line_number, line, 'Font line does not match \'font font-family\' or \'font "Font Family"\'')
                    font_name = match.group(1) or match.group(2)
                    queue.append(["font", font_name.replace('\\"', '"')])
                elif line.startswith('import '):
                    data = parse_import_line(line, line_number)
                    if FONT_FILE_PATTERN.search(data["path"]):
                        if not data["name"]:
                            raise_syntax_error(line_number, line, f'Importing a font file needs a name - use \'import "Font Name" {data["path"]}\'')
                        queue.append(["import", data["name"], data["path"]])
                    else:
                        if data["path"] not in stylesheets:
                            stylesheets.append(data["path"])
                        continue
                elif line.startswith('color '):
                    match = re.match(r'^color\s+(?:"((?:\\.|[^"\\])*)"|(.+))', line.strip())
                    if not match:
                        raise_syntax_error(line_number, line, "Color line does not match 'color color-value'")
                    color_value = match.group(1) or match.group(2)
                    queue.append(["color", color_value.replace('\\"', '"')])
                elif line.startswith('music '):
                    parts = line.strip().split(maxsplit=2)
                    if len(parts) < 2:
                        raise_syntax_error(line_number, line, "Music line needs a sub-command - 'music play path', 'music pause', or 'music stop'")
                    cmd = ["music", parts[1]]
                    if len(parts) == 3:
                        audio = parts[2]
                        if audio.startswith('url(') and audio.endswith(')'):
                            audio = audio[4:-1].strip('"\'')
                        cmd.append(audio)
                    queue.append(cmd)
                elif line.startswith('jump '):
                    jump_id = line[5:].strip()
                    if re.search(r'\s', jump_id):
                        raise_syntax_error(line_number, line, f'Jump id "{jump_id}" cannot contain spaces')
                    queue.append(["jump", jump_id])
                elif line.startswith('end '):
                    end_id = line[4:].strip()
                    if re.search(r'\s', end_id):
                        raise_syntax_error(line_number, line, f'End id "{end_id}" cannot contain spaces')
                    queue.append(["end", end_id])
                elif line.startswith('skip '):
                    skip_id = line[5:].strip()
                    if re.search(r'\s', skip_id):
                        raise_syntax_error(line_number, line, f'Skip id "{skip_id}" cannot contain spaces')
                    queue.append(["skip", skip_id])
                else:
                    raise_syntax_error(line_number, line, f'Unknown command "{line.split()[0]}"')

                queue_lines.append(line_number)
                queue_source.append(line)

        validate_jumps(queue, queue_lines, queue_source)
        queue_json = json.dumps(queue)
        stylesheet_links = "\n".join(
            f'        <link rel="stylesheet" href="{href.replace("&", "&amp;")}">'
            for href in stylesheets
        )
        html = """<!doctype html>
<html>
    <head>
        <title>%s</title>
%s
        <style>
            body,
            html {
                margin: 0;
                padding: 0;
            }

            body {
                background-color: black;
                display: grid;
                place-items: center;
                width: 100vw;
                height: 100vh;
                overflow: hidden;
            }

            #canvas {
                box-sizing: border-box;
                background-color: white;
                aspect-ratio: 4 / 3;
                width: min(100vw, 177.78vh);
                height: min(100vh, 56.25vw);
                display: flex;
                container-type: inline-size;
                flex-direction: column;
            }

            .choice {
                display: flex;
                justify-content: center;
                gap: 7.5cqw;
                flex-wrap: wrap;
            }

            .choice p {
                cursor: pointer;
            }

            .choice-container {
                display: flex;
                flex-direction: column;
                margin-top: auto;
                margin-bottom: auto;
            }

            p,
            a {
                font-family: Georgia;
                margin: 2cqw;
                font-size: 3cqw;
            }

            .s {
                font-size: 3cqw;
            }

            .m {
                font-size: 4cqw;
            }

            .l {
                font-size: 6cqw;
            }

            .xl {
                font-size: 10cqw;
            }

            .xxl {
                font-size: 18cqw;
            }

            .vcenter {
                margin-top: auto;
                margin-bottom: auto;
            }

            .bottom {
                margin-top: auto;
            }

            .center {
                align-self: center;
            }

            .left {
                align-self: flex-start;
            }

            .right {
                align-self: flex-end;
            }

            .centeralign {
                text-align: center;
            }

            .rightalign {
                text-align: right;
            }
        </style>
    </head>
    <body>
        <div id="canvas"></div>
        <script>
            const canvas = document.getElementById("canvas");
            let queue = 
        """ % (title or filepath[:-len(".woas")], stylesheet_links)
        html += queue_json + ";\n"
        html += """
            let choiceActive = false;
            let currentFont = "Georgia";
            let currentColor = "black";
            let music = new Audio();

            function doFirstQueue() {
                let firstqueue = queue[0];

                if (!firstqueue) {
                    canvas.replaceChildren();
                    return;
                }

                if (firstqueue[0] == "text") {
                    const text = document.createElement("p");

                    text.textContent = firstqueue[1];
                    text.className = firstqueue[2];
                    text.style.color = firstqueue[3] ?? currentColor;
                    text.style.fontFamily = firstqueue[4] ?? currentFont;
                    canvas.replaceChildren(text);
                    return;
                } else if (firstqueue[0] == "bg") {
                    canvas.style.background = firstqueue[1];
                    canvas.style.backgroundSize = "cover";
                    canvas.style.backgroundPosition = "center";
                    queue.shift();
                    doFirstQueue();
                    return;
                } else if (firstqueue[0] == "music") {
                    if (firstqueue[1] == "play") {
                        if (firstqueue[2]) {
                            music.pause();
                            music = new Audio(firstqueue[2]);
                        }
                        music.loop = true;
                        music.play();
                    } else if (firstqueue[1] == "stop") {
                        music.pause();
                        music.currentTime = 0;
                    } else if (firstqueue[1] == "pause") {
                        music.pause();
                    }
                    queue.shift();
                    doFirstQueue();
                    return;
                } else if (firstqueue[0] == "choice") {
                    choiceActive = true;
                    let promptText = firstqueue[1];
                    let optionsArray = firstqueue[2];
                    let textColor = firstqueue[3] ?? currentColor;

                    let container = document.createElement("div");
                    container.className = "choice-container";

                    let promptParagraph = document.createElement("p");
                    promptParagraph.className = "l center";
                    promptParagraph.innerText = promptText;
                    promptParagraph.style.color = textColor;
                    promptParagraph.style.fontFamily = currentFont;
                    container.appendChild(promptParagraph);

                    let choiceDiv = document.createElement("div");
                    choiceDiv.className = "choice";

                    optionsArray.forEach((option) => {
                        let optionButton = document.createElement("p");
                        optionButton.className = "m";
                        optionButton.innerText = option.text;
                        optionButton.style.color = textColor;
                        optionButton.style.fontFamily = currentFont;

                        optionButton.addEventListener("click", function (e) {
                            e.stopPropagation();

                            while (
                                queue.length > 0 &&
                                !(
                                    queue[0][0] === "jump" &&
                                    queue[0][1] === option.jump
                                )
                            ) {
                                queue.shift();
                            }

                            if (queue.length > 0) {
                                queue.shift();
                            }

                            choiceActive = false;
                            doFirstQueue();
                        });

                        choiceDiv.appendChild(optionButton);
                    });

                    container.appendChild(choiceDiv);
                    canvas.replaceChildren(container);
                    return;
                } else if (firstqueue[0] == "jump") {
                    while (
                        queue.length > 0 &&
                        !(
                            queue[0][0] === "end" &&
                            queue[0][1] === firstqueue[1]
                        )
                    ) {
                        queue.shift();
                    }

                    if (queue.length > 0) {
                        queue.shift();
                        doFirstQueue();
                    }

                    return;
                } else if (firstqueue[0] == "skip") {
                    while (
                        queue.length > 0 &&
                        !(
                            queue[0][0] === "jump" &&
                            queue[0][1] === firstqueue[1]
                        )
                    ) {
                        queue.shift();
                    }

                    if (queue.length > 0) {
                        queue.shift();
                        doFirstQueue();
                    }

                    return;
                } else if (firstqueue[0] == "font") {
                    currentFont = firstqueue[1];
                    queue.shift();
                    doFirstQueue();
                    return;
                } else if (firstqueue[0] == "import") {
                    const fontFace = new FontFace(
                        firstqueue[1],
                        `url("${firstqueue[2]}")`,
                    );

                    fontFace
                        .load()
                        .then((loadedFace) => {
                            document.fonts.add(loadedFace);
                        })
                        .catch((err) => {
                            console.error(
                                `Failed to load font "${firstqueue[1]}":`,
                                err,
                            );
                        })
                        .finally(() => {
                            queue.shift();
                            doFirstQueue();
                        });
                    return;
                } else if (firstqueue[0] == "color") {
                    currentColor = firstqueue[1];
                    queue.shift();
                    doFirstQueue();
                    return;
                } else {
                    queue.shift();
                    doFirstQueue();
                    return;
                }
            }

            doFirstQueue();

            document.addEventListener("keydown", (event) => {
                if (event.repeat) return;

                if (event.code === "Space" && !choiceActive) {
                    queue.shift();
                    doFirstQueue();
                }
            });

            canvas.addEventListener("click", () => {
                if (!choiceActive) {
                    queue.shift();
                    doFirstQueue();
                }
            });
        </script>
    </body>
</html>
        """

        output_filepath = filepath[:-len(".woas")] + ".html"
        with open(output_filepath, 'w') as out_file:
            out_file.write(html)
            
        print(f"Success! Game compiled to: {output_filepath}")
    except Exception as e:
        print(f"Game failed to compile: {e}")

if not file_path.endswith(".woas"):
    print("Error: File must be a .woas file!")
elif not os.path.isfile(file_path):
    print("Error: File does not exist!")
else:
    compile_game_from_file(file_path)