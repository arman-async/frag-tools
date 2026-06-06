import json
from pathlib import Path

INPUTS = {
    "NAME": (str, "Enter NAME Config [str]: "),
    "ADDRESS": (str, "Enter ADDRESS Config [str]: "),
    "HOST": (str,  "Enter HOST Config [str]: "),
    "PORT": (int, "Enter PORT Config [int]: "),
    "UUID": (str, "Enter UUID Config [str]: "),
    "SIN": (str, "Enter SIN Config [str]: "),
    "PATH": (str, "Enter PATH Config [str]: "),
}


def get_inputs(sample: dict = INPUTS) -> dict:
    config = {}
    for key, _ in sample.items():
        tp, question = _
        while True:
            answer = input(question)
            if tp == int:
                try:
                    answer = int(answer)
                except ValueError:
                    print("Invalid Type !!")
                    continue
            config[key] = answer
            break
    return config


def gen_config(inputs: dict, template: str) -> str:
    for key, value in inputs.items():
        if type(value) is int:
            template = template.replace('"{{' + key + '}}"', str(value))
        template = template.replace('"{{' + key + '}}"', f'"{value}"')
    return template


def main():
    template = Path("example.json").read_text()
    v = get_inputs(INPUTS)
    config = gen_config(v, template)
    file = Path(f"{v.get('NAME')}.json")
    with open(file, 'w', encoding='utf-8') as f:
        f.write(config)

if __name__ == "__main__":
    main()

