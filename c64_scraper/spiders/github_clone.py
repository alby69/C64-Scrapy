import os
import re
import hashlib
import logging
from pathlib import Path
from typing import Optional

import scrapy
from scrapy.http import Response

log = logging.getLogger("github_clone")

REPO_LIST = [
    ("digitsensitive_c64", "https://github.com/digitsensitive/c64"),
    ("ktuukkan_c64-asm", "https://github.com/ktuukkan/c64-asm"),
    ("dani-Tb_c64-asm-samples", "https://github.com/dani-Tb/c64-asm-samples"),
    ("nealvis_c64_samples_kick", "https://github.com/nealvis/c64_samples_kick"),
    ("nealvis_nv_c64_util", "https://github.com/nealvis/nv_c64_util"),
    ("kindjie_6502Assembly", "https://github.com/kindjie/6502Assembly"),
    ("bryancandi_Commodore", "https://github.com/bryancandi/Commodore"),
    ("benmcevoy_c64", "https://github.com/benmcevoy/c64"),
    ("JohanSmet_c64_experiments", "https://github.com/JohanSmet/c64_experiments"),
    (
        "petriw_Commodore64Programming",
        "https://github.com/petriw/Commodore64Programming",
    ),
    ("spiroharvey_c64", "https://github.com/spiroharvey/c64"),
    ("mwenge_iridisalpha", "https://github.com/mwenge/iridisalpha"),
    ("mwenge_gridrunner", "https://github.com/mwenge/gridrunner"),
    ("mwenge_matrix", "https://github.com/mwenge/matrix"),
    (
        "mwenge_attack-of-the-mutant-camels",
        "https://github.com/mwenge/attack-of-the-mutant-camels",
    ),
    ("mwenge_batalyx", "https://github.com/mwenge/batalyx"),
    ("mwenge_metagalactic-llamas", "https://github.com/mwenge/metagalactic-llamas"),
    (
        "Piddewitt_C64-Game-Source-Code",
        "https://github.com/Piddewitt/C64-Game-Source-Code",
    ),
    ("mist64_cbmsrc", "https://github.com/mist64/cbmsrc"),
    ("barryw_c64lib", "https://github.com/barryw/c64lib"),
    ("martinpiper_ACME", "https://github.com/martinpiper/ACME"),
    ("c64lib_common", "https://github.com/c64lib/common"),
    ("c64lib_chipset", "https://github.com/c64lib/chipset"),
    ("c64lib_text", "https://github.com/c64lib/text"),
    ("c64lib_copper64", "https://github.com/c64lib/copper64"),
    ("maciejmalecki_trex64", "https://github.com/maciejmalecki/trex64"),
    ("maciejmalecki_tony-demo", "https://github.com/maciejmalecki/tony-demo"),
    ("maciejmalecki_bluevessel", "https://github.com/maciejmalecki/bluevessel"),
    ("smnjameson_c64", "https://github.com/smnjameson/c64"),
    ("cliffordcarnmo_c64", "https://github.com/cliffordcarnmo/c64"),
    ("mrohmer_c64-assembly", "https://github.com/mrohmer/c64-assembly"),
    ("lhz_c64", "https://github.com/lhz/c64"),
    ("jblang_c64", "https://github.com/jblang/c64"),
    ("bitshifters_c64-fun", "https://github.com/bitshifters/c64-fun"),
    ("EngineersNeedArt_c64", "https://github.com/EngineersNeedArt/c64"),
]

ASM_EXTENSIONS = {".asm", ".a", ".s", ".inc", ".acme", ".kick", ".ka", ".src", ".lst"}


class GithubCloneSpider(scrapy.Spider):
    name = "github_clone"
    allowed_domains = ["github.com", "api.github.com", "raw.githubusercontent.com"]

    def __init__(
        self,
        repos: Optional[list] = None,
        output_dir: str = "data/src",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.repos = repos or REPO_LIST
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.seen_hashes: set[str] = set()

    def start_requests(self):
        for name, url in self.repos:
            repo_path = url.replace("https://github.com/", "")
            api_url = (
                f"https://api.github.com/repos/{repo_path}/git/trees/main?recursive=1"
            )
            yield scrapy.Request(
                url=api_url,
                callback=self.parse_tree,
                meta={"repo_name": name, "repo_url": url},
                headers={"Accept": "application/vnd.github+json"},
            )

    def parse_tree(self, response: Response):
        repo_name = response.meta["repo_name"]
        data = response.json()
        asm_files = []

        for item in data.get("tree", []):
            path = item.get("path", "")
            ext = Path(path).suffix.lower()
            if ext in ASM_EXTENSIONS and ".git" not in path:
                asm_files.append(item)

        log.info(f"  {repo_name}: {len(asm_files)} file ASM trovati")

        for item in asm_files:
            raw_url = f"https://raw.githubusercontent.com/{response.meta['repo_url'].replace('https://github.com/', '')}/main/{item['path']}"
            yield scrapy.Request(
                url=raw_url,
                callback=self.parse_asm_file,
                meta={"repo_name": repo_name, "path": item["path"]},
            )

    def parse_asm_file(self, response: Response):
        repo_name = response.meta["repo_name"]
        file_path = response.meta["path"]
        content = response.body

        h = hashlib.md5(content).hexdigest()[:8]
        if h in self.seen_hashes:
            return
        self.seen_hashes.add(h)

        repo_dir = self.output_dir / repo_name
        repo_dir.mkdir(parents=True, exist_ok=True)

        dest = repo_dir / Path(file_path).name
        if dest.exists():
            stem = dest.stem
            suffix = dest.suffix
            counter = 1
            while dest.exists():
                dest = repo_dir / f"{stem}_{counter}{suffix}"
                counter += 1

        dest.write_bytes(content)
        log.info(f"    Salvato: {dest}")
