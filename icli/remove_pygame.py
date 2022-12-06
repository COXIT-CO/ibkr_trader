def remove_pygame_occurencies(file_path):
    """
    given the path to file open it and remove all the code related to pygame module
    """
    lines: list
    with open(file_path, "r") as f:
        lines = f.readlines()
    
    is_code_block = False
    accumulative_string = "..."
    for i, line in enumerate(lines):
        spaces = len(line) - len(line.lstrip(" "))
        if "if" in line.lower() and "pygame" in line.lower():
            lines[i] = spaces * " " + "if False:\n"
        elif "pygame" in line.lower():
            if not is_code_block:
                is_code_block = True
            lines[i] = str()
            if len(accumulative_string) == 3:
                accumulative_string = " " * spaces + accumulative_string
        elif spaces <= len(accumulative_string) - len(accumulative_string.lstrip(" ")) and is_code_block:
            lines[i-1] = accumulative_string + "\n"
            accumulative_string = "..."
            is_code_block = False
        elif spaces > len(accumulative_string) - len(accumulative_string.lstrip(" ")) and is_code_block:
            lines[i] = str()

        
    with open(file_path, "w") as f:
        for line in lines:
            f.write(line)

    return lines


if __name__ == "__main__":
    remove_pygame_occurencies("icli/cli.py")
    remove_pygame_occurencies("icli/lang.py")
