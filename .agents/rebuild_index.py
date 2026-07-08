#!/usr/bin/env python3
import os
import json
import re

def parse_yaml_frontmatter(file_path):
    """
    Robust YAML frontmatter parser that handles simple key-value pairs,
    quoted strings, multi-line strings, and list structures.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", content, re.DOTALL)
    if not match:
        return {}
        
    frontmatter_text = match.group(1)
    data = {}
    current_key = None
    
    for line in frontmatter_text.splitlines():
        line_strip = line.strip()
        if not line_strip or line_strip.startswith("#"):
            continue
            
        # Check if it is a list element
        if line_strip.startswith("-"):
            if current_key:
                val = line_strip[1:].strip().strip('"').strip("'")
                if not isinstance(data.get(current_key), list):
                    data[current_key] = []
                data[current_key].append(val)
            continue
            
        # Parse Key: Value
        if ":" in line:
            parts = line.split(":", 1)
            key = parts[0].strip()
            val = parts[1].strip()
            
            # Remove inline comments
            if "#" in val and not (val.startswith('"') or val.startswith("'")):
                val = val.split("#", 1)[0].strip()
                
            val = val.strip('"').strip("'")
            
            if val == "":
                # Could be start of list or block
                data[key] = []
                current_key = key
            else:
                data[key] = val
                current_key = key
        elif current_key and line.startswith("  "):
            # Multi-line string continuation
            val = line.strip().strip('"').strip("'")
            if isinstance(data.get(current_key), str):
                data[current_key] += " " + val
            elif isinstance(data.get(current_key), list):
                data[current_key].append(val)
                
    return data

def infer_category(name):
    name_lower = name.lower()
    if any(k in name_lower for k in ["debug", "error", "trace", "diagnostics", "troubleshooter", "revert"]):
        return "debugging"
    elif any(k in name_lower for k in ["architect", "design", "plan", "records", "strategy", "roadmap"]):
        return "planning"
    elif any(k in name_lower for k in ["test", "testing", "review", "validator", "observability", "compliance", "audit"]):
        return "quality"
    elif any(k in name_lower for k in ["conductor", "orchestration", "using-superpowers", "writing-skills", "skillweave"]):
        return "meta"
    elif any(k in name_lower for k in ["deployment", "pipeline", "cicd", "automation", "upgrade", "changelog"]):
        return "delivery"
    return "implementation"

def generate_triggers(name, description):
    triggers = [name, name.replace("-", " ")]
    if description:
        clean_desc = re.sub(r"[^\w\s-]", "", description.lower())
        words = clean_desc.split()
        keywords = [w for w in words if len(w) > 4 and w not in ["about", "their", "there", "would", "should", "could", "build", "using", "write", "feature"]]
        for kw in keywords[:3]:
            if kw not in triggers:
                triggers.append(kw)
    return triggers

def rebuild_all():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(script_dir) == ".agents":
        superpowers_dir = os.path.join(script_dir, "plugins", "superpowers")
    else:
        superpowers_dir = os.path.join(script_dir, ".agents", "plugins", "superpowers")
        
    skills_dir = os.path.join(superpowers_dir, "skills")
    library_dir = os.path.join(superpowers_dir, "library")
    
    all_skills = []
    
    # Visible skills/
    if os.path.exists(skills_dir):
        for item in os.listdir(skills_dir):
            item_path = os.path.join(skills_dir, item)
            if os.path.isdir(item_path):
                skill_file = os.path.join(item_path, "SKILL.md")
                if os.path.exists(skill_file):
                    meta = parse_yaml_frontmatter(skill_file)
                    if not meta:
                        continue
                    
                    name = meta.get("name", item)
                    desc = meta.get("description", "")
                    
                    # Convert fields safely
                    atomic_val = meta.get("atomic", True)
                    atomic = atomic_val is True or str(atomic_val).lower() == "true"
                    
                    skill_entry = {
                        "name": name,
                        "description": desc,
                        "triggers": meta.get("triggers", [name, name.replace("-", " ")]),
                        "outputs": meta.get("outputs", ["implementation"]),
                        "depends_on": meta.get("depends_on", []),
                        "next_skills": meta.get("next_skills", []),
                        "atomic": atomic,
                        "path": f"skills/{item}/SKILL.md",
                        "category": meta.get("category", "meta")
                    }
                    all_skills.append(skill_entry)

    # Hidden library/
    if os.path.exists(library_dir):
        for item in os.listdir(library_dir):
            item_path = os.path.join(library_dir, item)
            if os.path.isdir(item_path):
                skill_file = os.path.join(item_path, "SKILL.md")
                if os.path.exists(skill_file):
                    meta = parse_yaml_frontmatter(skill_file)
                    if not meta:
                        continue
                    
                    name = meta.get("name", item)
                    desc = meta.get("description", "")
                    
                    triggers = meta.get("triggers")
                    if not triggers or not isinstance(triggers, list):
                        triggers = generate_triggers(name, desc)
                        
                    outputs = meta.get("outputs", ["working-code"])
                    depends_on = meta.get("depends_on", [])
                    next_skills = meta.get("next_skills", [])
                    
                    atomic_val = meta.get("atomic", True)
                    atomic = atomic_val is True or str(atomic_val).lower() == "true"
                    
                    category = meta.get("category", infer_category(name))
                    
                    skill_entry = {
                        "name": name,
                        "description": desc,
                        "triggers": triggers,
                        "outputs": outputs,
                        "depends_on": depends_on,
                        "next_skills": next_skills,
                        "atomic": atomic,
                        "path": f"library/{item}/SKILL.md",
                        "category": category
                    }
                    all_skills.append(skill_entry)

    # Sort
    all_skills.sort(key=lambda s: s["name"])
    
    # Save
    output_index_path = os.path.join(skills_dir, "skill-index.json")
    with open(output_index_path, "w", encoding="utf-8") as f:
        json.dump({"skills": all_skills}, f, indent=2, ensure_ascii=False)
        
    print(f"[+] Rebuilt skill-index.json successfully! Total skills indexed: {len(all_skills)}")

if __name__ == "__main__":
    rebuild_all()
