import re
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
        # next up - converting queue from array into string that can be put into js
        return
    except Exception as e:
        print(e)

compile_game_from_file(file_path)