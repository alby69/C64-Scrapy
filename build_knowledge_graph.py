#!/usr/bin/env python3
import pathlib
import re
import json
import yaml

COMMON_REGISTERS = {
    "$D020": {"name": "Border Color", "hw": "VIC-II", "ref": "sta_c64/cbm64mem.md#d020"},
    "$D021": {"name": "Background Color", "hw": "VIC-II", "ref": "sta_c64/cbm64mem.md#d021"},
    "$D011": {"name": "VIC Control Register 1", "hw": "VIC-II", "ref": "sta_c64/cbm64mem.md#d011"},
    "$D012": {"name": "Raster Counter", "hw": "VIC-II", "ref": "sta_c64/cbm64mem.md#d012"},
    "$D015": {"name": "Sprite Enable Register", "hw": "VIC-II", "ref": "sta_c64/cbm64mem.md#d015"},
    "$D016": {"name": "VIC Control Register 2", "hw": "VIC-II", "ref": "sta_c64/cbm64mem.md#d016"},
    "$D018": {"name": "Memory Setup Register", "hw": "VIC-II", "ref": "sta_c64/cbm64mem.md#d018"},
    "$DC00": {"name": "CIA 1 Port A (Joystick 2, Keyboard)", "hw": "CIA", "ref": "sta_c64/cbm64mem.md#dc00"},
    "$DC01": {"name": "CIA 1 Port B (Joystick 1, Keyboard)", "hw": "CIA", "ref": "sta_c64/cbm64mem.md#dc01"},
    "$FFD2": {"name": "CHROUT (Output Character)", "hw": "KERNAL", "ref": "sta_c64/cbm64mem.md#ffd2"},
    "$FFE4": {"name": "GETIN (Get Character)", "hw": "KERNAL", "ref": "sta_c64/cbm64mem.md#ffe4"},
    "$0314": {"name": "IRQ Vector", "hw": "KERNAL", "ref": "sta_c64/cbm64mem.md#0314"},
}

def load_frontmatter_and_content(file_path: pathlib.Path):
    try:
        text = file_path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            return {}, text
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return yaml.safe_load(parts[1]) or {}, parts[2]
        return {}, text
    except Exception:
        return {}, ""

def build_knowledge_graph(docs_dir: pathlib.Path, output_json: pathlib.Path):
    nodes = []
    edges = []
    seen_nodes = set()

    def add_node(node_id, node_type, label):
        if node_id not in seen_nodes:
            seen_nodes.add(node_id)
            nodes.append({"id": node_id, "type": node_type, "label": label})

    # Add standard hardware nodes
    for hw in ["VIC-II", "SID", "CIA", "CPU", "KERNAL", "BASIC ROM"]:
        add_node(hw, "hardware", hw)

    # Add topic-to-hardware relations
    topic_hw_relations = {
        "raster interrupts": "VIC-II",
        "sprite programming": "VIC-II",
        "graphics": "VIC-II",
        "sound generation": "SID",
        "input handling": "CIA",
        "memory management": "CPU",
        "assembly": "CPU",
        "basic": "BASIC ROM"
    }

    for topic, hw in topic_hw_relations.items():
        add_node(topic, "topic", topic)
        edges.append({"source": topic, "target": hw, "relation": "managed_by_hardware"})

    if not docs_dir.exists():
        print(f"[avviso] la cartella {docs_dir} non esiste. Impossibile generare il grafo.")
        return

    # Iterate documents
    for md_path in sorted(docs_dir.rglob("*.md")):
        if md_path.name in ["index.md", "_combined.md"]:
            continue

        fm, body = load_frontmatter_and_content(md_path)
        if not fm:
            continue

        doc_id = md_path.relative_to(docs_dir).as_posix()
        title = fm.get("title", md_path.stem)

        add_node(doc_id, "document", title)

        # Link document to its explicit category
        category = fm.get("category", "reference")
        add_node(category, "category", category)
        edges.append({"source": doc_id, "target": category, "relation": "belongs_to_category"})

        # Link document to topics
        for topic in fm.get("topics", []):
            add_node(topic, "topic", topic)
            edges.append({"source": doc_id, "target": topic, "relation": "discusses_topic"})

        # Link document to hardware
        for hw in fm.get("hardware", []):
            add_node(hw, "hardware", hw)
            edges.append({"source": doc_id, "target": hw, "relation": "targets_hardware"})

        # Scan body for memory address registers
        found_regs = []
        for reg, info in COMMON_REGISTERS.items():
            pattern = re.escape(reg)
            if re.search(pattern, body, re.IGNORECASE) or re.search(pattern, title, re.IGNORECASE):
                found_regs.append((reg, info))

        if found_regs:
            # 1. Append links to the bottom of the document if not already modified
            if "### Collegamenti e Riferimenti Hardware" not in body:
                extra_links = "\n\n### Collegamenti e Riferimenti Hardware\n"
                for reg, info in found_regs:
                    # Let's adjust reference to find file properly in the folder structure
                    ref_link = "../" + info['ref'] if "/" in doc_id else info['ref']
                    extra_links += f"- **{reg} ({info['name']})**: Associato al chip {info['hw']}. Vedere [Mappa di Memoria]({ref_link}).\n"

                # Rewrite file
                new_text = "---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + "---\n" + body + extra_links
                md_path.write_text(new_text, encoding="utf-8")

            # 2. Add register nodes and connect to document
            for reg, info in found_regs:
                reg_node_id = f"register_{reg}"
                add_node(reg_node_id, "register", f"{reg} - {info['name']}")
                edges.append({"source": doc_id, "target": reg_node_id, "relation": "references_register"})
                edges.append({"source": reg_node_id, "target": info["hw"], "relation": "part_of_hardware"})

    # Write knowledge graph to json
    output_json.parent.mkdir(parents=True, exist_ok=True)
    graph_data = {"nodes": nodes, "edges": edges}
    output_json.write_text(json.dumps(graph_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Grafo di conoscenza generato con successo: {output_json} ({len(nodes)} nodi, {len(edges)} archi)")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Costruisce il Knowledge Graph dai file Markdown")
    parser.add_argument("--docs", default="docs_c64", help="Cartella con i file Markdown")
    parser.add_argument("--out", default="dataset_c64/knowledge_graph.json", help="File JSON di output")
    args = parser.parse_args()
    build_knowledge_graph(pathlib.Path(args.docs), pathlib.Path(args.out))
