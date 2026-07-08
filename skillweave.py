#!/usr/bin/env python3
import os
import sys
import json
import re
import urllib.request
import urllib.error

def load_env():
    env_vars = {}
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_path):
        # Fallback to .env.example if .env doesn't exist
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env.example")
    
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("=", 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip()
                    # Strip quotes if present
                    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                    env_vars[key] = val
    return env_vars

def call_llm(prompt, env):
    provider = env.get("SKILLWEAVE_PROVIDER", "lmstudio").lower()
    model = env.get("SKILLWEAVE_MODEL", "")
    api_key = env.get("SKILLWEAVE_API_KEY", "")
    base_url = env.get("SKILLWEAVE_BASE_URL", "http://localhost:1234/v1")
    temp = float(env.get("SKILLWEAVE_TEMPERATURE", "0.1"))
    max_tokens = int(env.get("SKILLWEAVE_MAX_TOKENS", "4096"))

    headers = {"Content-Type": "application/json"}
    payload = {}

    if provider == "gemini":
        # Gemini OpenAI compatibility or direct API
        url = base_url if base_url else "https://generativelanguage.googleapis.com/v1beta/openai/v1/chat/completions"
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY", "")
        headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temp,
            "max_tokens": max_tokens
        }
    elif provider == "anthropic":
        url = base_url if base_url else "https://api.anthropic.com/v1/messages"
        headers["x-api-key"] = api_key
        headers["anthropic-version"] = "2023-06-01"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temp
        }
    elif provider in ["openai", "lmstudio", "ollama"]:
        if provider == "openai":
            url = base_url if base_url else "https://api.openai.com/v1/chat/completions"
            headers["Authorization"] = f"Bearer {api_key}"
        elif provider == "lmstudio":
            url = base_url if base_url else "http://localhost:1234/v1/chat/completions"
        else: # ollama
            url = base_url if base_url else "http://localhost:11434/v1/chat/completions"
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temp,
            "max_tokens": max_tokens
        }
    else:
        # Fallback to OpenAI compatible custom endpoint
        if not base_url:
            print("Error: SKILLWEAVE_BASE_URL must be specified for custom providers.", file=sys.stderr)
            sys.exit(1)
        url = base_url
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temp
        }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            
            # Parse response content depending on format
            if "choices" in res_data:
                return res_data["choices"][0]["message"]["content"]
            elif "content" in res_data:
                # Anthropic message content structure
                if isinstance(res_data["content"], list):
                    return res_data["content"][0]["text"]
                return res_data["content"]
            else:
                return json.dumps(res_data)
    except urllib.error.URLError as e:
        print(f"Error communicating with the LLM API ({provider}): {e}", file=sys.stderr)
        if hasattr(e, 'read'):
            print(f"Response: {e.read().decode('utf-8')}", file=sys.stderr)
        sys.exit(1)

def run_sad_pipeline(user_query, env):
    print(f"[*] Starting SkillWeave SAD routing pipeline...")
    print(f"[*] Provider: {env.get('SKILLWEAVE_PROVIDER', 'lmstudio')} | Model: {env.get('SKILLWEAVE_MODEL', 'local-model')}")

    # Load paths
    index_path = env.get("SKILLWEAVE_SKILL_INDEX_PATH", ".agents/plugins/superpowers/skills/skill-index.json")
    dag_path = env.get("SKILLWEAVE_SKILL_DAG_PATH", ".agents/plugins/superpowers/skills/skill-dag.json")
    
    # Resolve paths relative to workspace root
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_index_path = os.path.join(base_dir, index_path)
    full_dag_path = os.path.join(base_dir, dag_path)

    if not os.path.exists(full_index_path):
        print(f"Error: skill-index.json not found at {full_index_path}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(full_dag_path):
        print(f"Error: skill-dag.json not found at {full_dag_path}", file=sys.stderr)
        sys.exit(1)

    with open(full_index_path, "r", encoding="utf-8") as f:
        skill_index = json.load(f)
    
    with open(full_dag_path, "r", encoding="utf-8") as f:
        skill_dag = json.load(f)

    # 1. Decompose
    print("[*] Phase 1: Iterative Skill-Aware Decomposition (SAD)...")
    skills_summary = []
    for s in skill_index["skills"]:
        skills_summary.append({
            "name": s["name"],
            "description": s["description"],
            "triggers": s["triggers"]
        })

    decomposition_prompt = f"""You are the SkillWeave SAD Router.
Your job is to decompose the user's request into atomic sub-tasks that align EXACTLY with the available skills in our library.

Available Skills in our library:
{json.dumps(skills_summary, indent=2)}

User request: "{user_query}"

Instructions:
1. Decompose the request into atomic steps.
2. For each step, map it to exactly one available skill.
3. If a step does not map to any available skill, you MUST re-decompose or combine it until all steps align perfectly with available skills (Decomposition Alignment = 1.0).
4. Output your answer in JSON format containing:
   - "decomposition_alignment": float (alignment ratio from 0.0 to 1.0)
   - "steps": list of objects containing:
     - "subtask": description of the step
     - "skill": the matched skill name
     - "rationale": brief explanation of why this skill fits the sub-task

Output ONLY valid JSON.
"""
    
    res_text = call_llm(decomposition_prompt, env)
    
    # Try to find JSON block in output
    json_match = re.search(r"({.*})", res_text, re.DOTALL)
    if json_match:
        try:
            sad_data = json.loads(json_match.group(1))
        except Exception:
            sad_data = {"steps": [], "decomposition_alignment": 0.0}
    else:
        sad_data = {"steps": [], "decomposition_alignment": 0.0}

    print(f"  DA Score: {sad_data.get('decomposition_alignment', 0.0)}")
    for i, step in enumerate(sad_data.get("steps", [])):
        print(f"  - Step {i+1}: {step.get('subtask')} -> [{step.get('skill')}]")

    # 2. Retrieve
    print("\n[*] Phase 2: Retrieval...")
    required_skills = list(set([step.get("skill") for step in sad_data.get("steps", [])]))
    print(f"  Skills retrieved: {', '.join(required_skills)}")

    # 3. Compose
    print("\n[*] Phase 3: Composition & DAG Ordering...")
    edges = skill_dag.get("edges", [])
    
    # Simple topological sort for the retrieved skills
    ordered_skills = []
    visited = set()
    temp_visited = set()

    def visit(node):
        if node in temp_visited:
            return # Cycle detected or duplicate
        if node not in visited:
            temp_visited.add(node)
            # Find dependencies
            deps = [edge["from"] for edge in edges if edge["to"] == node]
            for dep in deps:
                if dep in required_skills:
                    visit(dep)
            temp_visited.remove(node)
            visited.add(node)
            ordered_skills.append(node)

    for skill in required_skills:
        visit(skill)

    print("  Composed Execution Plan (DAG Order):")
    for i, skill in enumerate(ordered_skills):
        # Find the path in skill-index
        skill_info = next((s for s in skill_index["skills"] if s["name"] == skill), None)
        path = skill_info["path"] if skill_info else "Unknown"
        print(f"  {i+1}. [{skill}] (Source path: {path})")

    print("\n[+] Routing completed successfully! Provide this execution plan to your agent to load the respective skills.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python skillweave.py \"<user request>\"")
        sys.exit(1)
        
    query = sys.argv[1]
    env_config = load_env()
    run_sad_pipeline(query, env_config)
