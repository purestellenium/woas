import re, json, os

file_path = input("Path to .woas file: ").strip()

def parse_text_line(line):
    pattern = r'^"((?:\\.|[^"\\])*)"\s*(.*?)(?:\s*/\s*(\S+)(?:\s+(.*))?)?$'
    match = re.match(pattern, line.strip())
    
    if not match:
        raise SyntaxError(f"Line does not match required syntax: {line}")
        
    text = match.group(1).replace('\\"', '"')
    
    classes = match.group(2).strip() if match.group(2) else ""
    
    color = match.group(3)
    if color is None or color.lower() == "null":
        color = None
        
    font_family = match.group(4)
    if font_family is None or font_family.lower() == "null":
        font_family = None
        
    return {
        "text": text,
        "classes": classes,
        "color": color,
        "font_family": font_family
    }

def parse_choice_line(line):
    main_pattern = r'^choice\s+"((?:\\.|[^"\\])*)"\s*/\s*(.*)$'
    main_match = re.match(main_pattern, line.strip())
    
    if not main_match:
        raise SyntaxError(f"Choice line does not match required syntax: {line}")
        
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

def compile_game_from_file(filepath):
    try:
        title = None

        with open(filepath, 'r') as file:
            queue = []
            for line in file:
                if not line.strip():
                    continue
                
                if line[0] == '"':
                    to_insert = ["text"]
                    data = parse_text_line(line.strip())
                    to_insert.append(data["text"])
                    to_insert.append(data["classes"])
                    to_insert.append(data["color"])
                    to_insert.append(data["font_family"])
                    queue.append(to_insert)
                elif line.startswith('choice '):
                    data = parse_choice_line(line)
                    to_insert = [
                        "choice", 
                        data["prompt"], 
                        data["options"],
                        data["color"]
                    ]
                    queue.append(to_insert)
                elif line.startswith('title '):
                    match = re.match(r'^title\s+"((?:\\.|[^"\\])*)"', line.strip())
                    if match:
                        title = match.group(1).replace('\\"', '"')
                elif line.startswith('bg '):
                    bg_val = line[3:].strip()
                    if re.search(r'\.(png|jpg|jpeg|gif|webp)$', bg_val, re.I) and not bg_val.startswith('url('):
                        bg_val = f"url('{bg_val}')"
                    queue.append(["bg", bg_val])
                elif line.startswith('font '):
                    match = re.match(r'^font\s+(?:"((?:\\.|[^"\\])*)"|(.+))', line.strip())
                    if match:
                        font_name = match.group(1) or match.group(2)
                        queue.append(["font", font_name.replace('\\"', '"')])
                elif line.startswith('color '):
                    queue.append(["color", line[6:].strip().strip('"\'')])
                elif line.startswith('music '):
                    parts = line.strip().split(maxsplit=2)
                    if len(parts) >= 2:
                        cmd = ["music", parts[1]]
                        if len(parts) == 3:
                            audio = parts[2]
                            if audio.startswith('url(') and audio.endswith(')'):
                                audio = audio[4:-1].strip('"\'')
                            cmd.append(audio)
                        queue.append(cmd)
                        
                elif line.startswith('jump '):
                    queue.append(["jump", line[5:].strip()])
                    
                elif line.startswith('end '):
                    queue.append(["end", line[4:].strip()])
                else:
                    queue.append(line.split())
        queue_json = json.dumps(queue)
        html = """<!doctype html>
<html>
    <head>
        <title>%s</title>
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

            /* text sizes */

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

            /* positioning */

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
        """ % (title or filepath.replace(".woas", ""))
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
                            music = new Audio(firstqueue[2]);
                        }
                        music.loop = true;
                        music.play();
                    } else if (firstqueue[1] == "stop") {
                        music.pause();
                        music.currentTime = 0;
                    } else if (firstqueue[1] == "pause") {
                        music.pause();
                    } else {
                    }
                    queue.shift();
                    doFirstQueue();
                    return;
                } else if (firstqueue[0] == "choice") {
                    choiceActive = true;
                    let promptText = firstqueue[1];
                    let optionsArray = firstqueue[2];
                    let textColor = firstqueue[3];

                    let container = document.createElement("div");
                    container.className = "choice-container";

                    let promptParagraph = document.createElement("p");
                    promptParagraph.className = "l center";
                    promptParagraph.innerText = promptText;
                    if (textColor) {
                        promptParagraph.style.color = textColor;
                    }
                    container.appendChild(promptParagraph);

                    let choiceDiv = document.createElement("div");
                    choiceDiv.className = "choice";

                    optionsArray.forEach((option) => {
                        let optionButton = document.createElement("p");
                        optionButton.className = "m";
                        optionButton.innerText = option.text;

                        if (textColor) {
                            optionButton.style.color = textColor;
                        }

                        optionButton.addEventListener("click", function (e) {
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
                } else if (firstqueue[0] == "font") {
                    currentFont = firstqueue[1];
                    queue.shift();
                    doFirstQueue();
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
        </script>
    </body>
</html>
        """

        output_filepath = filepath.replace(".woas", ".html")
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