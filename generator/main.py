import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

CONFIG_JSON = Path("config.json")
DIR_PROTCOLS = Path("protocols")
CONFIG_EXMAPLE = DIR_PROTCOLS / Path("template.json")
FRAGMENT_TEMPALTE = """
{
    "protocol": "freedom",
    "settings": {
    "fragment": {
        "packets": "{{PACKETS}}",
        "length": "{{LENGTH}}",
        "interval": "{{INTERVAL}}",
        "maxSplit": "{{MAXSPLIT}}"
    }
    },
    "streamSettings": {
    "sockopt": {
        "domainStrategy": "UseIP",
        "happyEyeballs": {
        "tryDelayMs": 250,
        "prioritizeIPv6": false,
        "interleave": 2,
        "maxConcurrentTry": 4
        }
    }
    },
    "tag": "{{TAG}}"
}
"""


class Protocols(Enum):
    VLESS_WS_TLS = "vlees-ws-tls.json"


@dataclass
class ProxyConfig:
    protocol: Path
    address: str
    port: int
    host: str
    sin: str
    uuid: str
    path: str


@dataclass
class FragmentConfig:
    packets: str
    length: str
    interval: str
    maxSplit: str


@dataclass
class InputConfig:
    protocol: Protocols
    address: list[str]
    name: str
    port: int
    host: str
    sin: str
    uuid: str
    path: str
    strategy: str
    fragments: list[FragmentConfig]


def replace_json(values: dict, template: str, trasfrom_upper_key: bool = False) -> str:
    for key, value in values.items():
        if trasfrom_upper_key and type(key) is str:
            key = key.upper()
        if type(value) is int:
            template = template.replace('"{{' + key + '}}"', str(value))
        template = template.replace('"{{' + key + '}}"', f'"{value}"')
    return template


def upper_dict_key(d: dict) -> dict:
    if not isinstance(d, Mapping):
        return d

    result = {}

    for key, value in d.items():
        new_key = key.upper() if isinstance(key, str) else key

        if isinstance(value, Mapping):
            new_value = upper_dict_key(value)
        elif isinstance(value, list):
            new_value = [
                upper_dict_key(item) if isinstance(item, Mapping) else item
                for item in value
            ]
        else:
            new_value = value

        result[new_key] = new_value

    return result


class Generator:
    def __init__(
        self,
        proxy_conf: ProxyConfig,
        frag_conf: FragmentConfig,
        counter: int,
    ):
        self.counter = counter
        self.proxy_conf = proxy_conf
        self.frag_conf = frag_conf

    def proxy(self) -> dict:
        porotcol_template = self.proxy_conf.protocol.read_text()

        values = upper_dict_key(self.proxy_conf.__dict__)
        values["TAG"] = f"proxy-{self.counter}"
        values["FRAGMENT_ATTH"] = f"fragment-{self.counter}"
        json_str = replace_json(values, porotcol_template)
        return json.loads(json_str)

    def fragment(self) -> dict:
        fragment_template = FRAGMENT_TEMPALTE
        values = upper_dict_key(self.frag_conf.__dict__)
        values["TAG"] = f"fragment-{self.counter}"
        json_str = replace_json(values, fragment_template)
        return json.loads(json_str)


class ConfigPipeline:
    def __init__(self, config: InputConfig):
        self.config = config

    def build_proxy_config(self, address: str) -> ProxyConfig:
        base_data = {
            "host": self.config.host,
            "sin": self.config.sin,
            "uuid": self.config.uuid,
            "port": self.config.port,
            "path": self.config.path,
        }

        return ProxyConfig(
            **base_data,
            protocol=DIR_PROTCOLS / Path(self.config.protocol.value),
            address=address,
        )

    def build_fragment_config(self, index: int) -> FragmentConfig:
        fragment = self.config.fragments[index]
        return FragmentConfig(**fragment)

    def generate(self):

        for address in self.config.address:

            for index in range(len(self.config.fragments)):
                proxy_config = self.build_proxy_config(address)
                fragment_config = self.build_fragment_config(index)
                yield proxy_config, fragment_config


def load_input_config(config: Path) -> InputConfig:
    with open(config, "r", encoding="utf-8") as f:
        conf_dict = json.load(f)
    input_config = InputConfig(**conf_dict)
    input_config.protocol = Protocols.__dict__.get(input_config.protocol)
    return input_config


def main():
    input_config = load_input_config(CONFIG_JSON)
    pipeline = ConfigPipeline(input_config)
    outbounds = []
    for counter, _ in enumerate(pipeline.generate()):
        proxy_conf, frag_conf = _
        gen = Generator(proxy_conf, frag_conf, counter=counter)
        proxy = gen.proxy()
        frag = gen.fragment()
        outbounds.extend((proxy, frag))

    f = replace_json(input_config.__dict__, CONFIG_EXMAPLE.read_text(), True)
    f_d = json.loads(f)
    f_d["outbounds"] = outbounds
    with open(Path(f"{input_config.name}.json"), "w") as f:
        json.dump(f_d, f)


if __name__ == "__main__":
    main()
