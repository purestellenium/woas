import re, json
# this is going to be the main compiler script! passing a valid .woas file into this script should generate a valid game

file_path = input("Path to .woas file: ")

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

def compile_game_from_file(filepath):
    html = '''<!doctype html>
    <html>
    <head>
        <title>title</title>
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

            p {
                font-family: Georgia;
                margin: 2cqw;
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
            let queue = '''
    try:
        with open(filepath, 'r') as file:
            # generate queue
            queue = []
            for line in file:
                # handle each line
                if line[0] == '"':
                    # text case
                    to_insert = ["text"]
                    data = parse_text_line(line.strip())
                    to_insert.append(data["text"])
                    to_insert.append(data["classes"])
                    to_insert.append(data["color"])
                    to_insert.append(data["font_family"])
                    queue.append(to_insert)
                else:
                    # bg, music case
                    queue.append(line.split())
        # convert queue from array into string that can be put into js
        queue_json = json.dumps(queue)
        # finish out html
        html += queue_json + ";\n"
        html += """
            let currentFont = "Georgia";
            let currentColor = "blue";
            let music = new Audio();

            function doFirstQueue() {
                let firstqueue = queue[0];
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
                } else {
                    return;
                }
            }

            doFirstQueue();

            document.addEventListener("keydown", (event) => {
                if (event.repeat) return;

                if (event.code === "Space") {
                    // pops queue and refreshes screen
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

compile_game_from_file(file_path)