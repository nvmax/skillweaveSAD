#!/usr/bin/env python3
import os
import json
import re

def parse_frontmatter(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Match YAML frontmatter between --- and ---
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", content, re.DOTALL)
    if not match:
        return {}
    
    yaml_text = match.group(1)
    data = {}
    
    # Simple manual YAML parser (to avoid external PyYAML dependencies)
    current_key = None
    in_list = False
    
    for line in yaml_text.splitlines():
        line_strip = line.strip()
        if not line_strip:
            continue
        
        # Handle list items
        if line_strip.startswith("-"):
            val = line_strip[1:].strip().strip('"').strip("'")
            if current_key and isinstance(data.get(current_key), list):
                data[current_key].append(val)
            continue
        
        # Handle key: value or multi-line keys
        parts = line.split(":", 1)
        if len(parts) == 2:
            key = parts[0].strip()
            val = parts[1].strip().strip('"').strip("'")
            
            # Reset list context
            in_list = False
            
            if val == "":
                # Could be a list starts on next lines, or multi-line string
                data[key] = []
                current_key = key
            else:
                data[key] = val
                current_key = key
        elif current_key and line.startswith("  "):
            # Multi-line string value continuation
            val = line.strip().strip('"').strip("'")
            if isinstance(data[current_key], str):
                data[current_key] += " " + val
            elif isinstance(data[current_key], list):
                # Should have been caught by list item dash, but fallback
                data[current_key].append(val)
                
    return data

def infer_category(name):
    name_lower = name.lower()
    # Debugging / Error Handling
    if any(k in name_lower for k in ["debug", "error", "trace", "diagnostics", "troubleshooter", "revert"]):
        return "debugging"
    # Planning / Architecture
    elif any(k in name_lower for k in ["architect", "design", "plan", "records", "strategy", "roadmap"]):
        return "planning"
    # Quality / Testing / Reviews
    elif any(k in name_lower for k in ["test", "testing", "review", "validator", "observability", "compliance", "audit"]):
        return "quality"
    # Meta
    elif any(k in name_lower for k in ["conductor", "orchestration", "using-superpowers", "writing-skills", "skillweave"]):
        return "meta"
    # Delivery
    elif any(k in name_lower for k in ["deployment", "pipeline", "cicd", "automation", "upgrade", "changelog"]):
        return "delivery"
    # Default is implementation
    return "implementation"

def generate_triggers(name, description):
    triggers = [name, name.replace("-", " ")]
    
    # Extract terms from description
    if description:
        # Add interesting keywords
        clean_desc = re.sub(r"[^\w\s-]", "", description.lower())
        words = clean_desc.split()
        keywords = [w for w in words if len(w) > 4 and w not in ["about", "their", "there", "would", "should", "could", "build", "using", "write"]]
        for kw in keywords[:3]:
            if kw not in triggers:
                triggers.append(kw)
    return triggers

def rebuild_all():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    superpowers_dir = os.path.join(base_dir, ".agents", "plugins", "superpowers")
    skills_dir = os.path.join(superpowers_dir, "skills")
    library_dir = os.path.join(superpowers_dir, "library")
    
    all_skills = []
    
    # Process visible skills/
    for item in os.listdir(skills_dir):
        item_path = os.path.join(skills_dir, item)
        if os.path.isdir(item_path):
            skill_file = os.path.join(item_path, "SKILL.md")
            if os.path.exists(skill_file):
                meta = parse_frontmatter(skill_file)
                if not meta:
                    continue
                
                # Check for existing index structure
                name = meta.get("name", item)
                desc = meta.get("description", "")
                
                skill_entry = {
                    "name": name,
                    "description": desc,
                    "triggers": meta.get("triggers", [name, name.replace("-", " ")]),
                    "outputs": meta.get("outputs", ["implementation"]),
                    "depends_on": meta.get("depends_on", []),
                    "next_skills": meta.get("next_skills", []),
                    "atomic": meta.get("atomic", "true") == "true" or meta.get("atomic") is True,
                    "path": f"skills/{item}/SKILL.md",
                    "category": meta.get("category", "meta")
                }
                all_skills.append(skill_entry)

    # Process hidden library/
    for item in os.listdir(library_dir):
        item_path = os.path.join(library_dir, item)
        if os.path.isdir(item_path):
            skill_file = os.path.join(item_path, "SKILL.md")
            if os.path.exists(skill_file):
                meta = parse_frontmatter(skill_file)
                if not meta:
                    continue
                
                name = meta.get("name", item)
                desc = meta.get("description", "")
                
                # Retrieve triggers and dependencies if explicitly specified in frontmatter
                triggers = meta.get("triggers")
                if not triggers:
                    triggers = generate_triggers(name, desc)
                    
                outputs = meta.get("outputs", ["implementation"])
                depends_on = meta.get("depends_on", [])
                next_skills = meta.get("next_skills", [])
                
                # Read atomic as bool
                atomic_val = meta.get("atomic", "true")
                atomic = atomic_val == "true" or atomic_val is True
                
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

    # Sort skills by name
    all_skills.sort(key=lambda s: s["name"])
    
    # Save skill-index.json
    output_index_path = os.path.join(skills_dir, "skill-index.json")
    with open(output_index_path, "w", encoding="utf-8") as f:
        json.dump({"skills": all_skills}, f, indent=2, ensure_ascii=False)
        
    print(f"[+] Rebuilt skill-index.json successfully! Total skills indexed: {len(all_skills)}")

if __name__ == "__main__":
    rebuild_all()
