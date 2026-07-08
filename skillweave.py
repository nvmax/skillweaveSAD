#!/usr/bin/env python3
import os
import sys
import json
import re
import math
import urllib.request
import urllib.error

# List of common English stopwords to filter out for TF-IDF tokenization
STOPWORDS = set([
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "arent", "as", "at",
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "cant", "cannot", "could",
    "couldnt", "did", "didnt", "do", "does", "doesnt", "doing", "dont", "down", "during", "each", "few", "for", "from",
    "further", "had", "hadnt", "has", "hasnt", "have", "havent", "having", "he", "hed", "hell", "hes", "her", "here",
    "heres", "hers", "herself", "him", "himself", "his", "how", "hows", "i", "id", "ill", "im", "ive", "if", "in",
    "into", "is", "isnt", "it", "its", "itself", "lets", "me", "more", "most", "mustnt", "my", "myself", "no", "nor",
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own",
    "same", "shant", "she", "shed", "shell", "shes", "should", "shouldnt", "so", "some", "such", "than", "that",
    "thats", "the", "their", "theirs", "them", "themselves", "then", "there", "theres", "these", "they", "theyd",
    "theyll", "theyre", "theyve", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "wasnt", "we", "wed", "well", "were", "weve", "werent", "what", "whats", "when", "whens", "where", "wheres",
    "which", "while", "who", "whos", "whom", "why", "whys", "with", "wont", "would", "wouldnt", "you", "youd",
    "youll", "youre", "youve", "your", "yours", "yourself", "yourselves", "use", "using", "skill", "skills", "task",
    "tasks", "need", "needs", "want", "wants", "how-to", "guide", "expert", "specializing", "specialist"
])

def load_env():
    env_vars = {}
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_path):
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
                    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                    env_vars[key] = val
    return env_vars

def extract_json_block(text):
    """
    Robust JSON block extractor that strips markdown code fences and counts
    braces to locate and extract valid JSON objects or arrays.
    """
    # Clean up markdown code fences
    cleaned = re.sub(r"^```[a-zA-Z0-9]*\s*", "", text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())
    
    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
        
    # Find matching braces/brackets
    first_brace = cleaned.find("{")
    first_bracket = cleaned.find("[")
    
    start_idx = -1
    end_char = ""
    
    if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
        start_idx = first_brace
        start_char = "{"
        end_char = "}"
    elif first_bracket != -1:
        start_idx = first_bracket
        start_char = "["
        end_char = "]"
        
    if start_idx == -1:
        raise ValueError("Could not find any JSON structural braces or brackets in the response.")
        
    # Brace/bracket counting algorithm
    brace_count = 0
    in_string = False
    escape = False
    
    for i in range(start_idx, len(cleaned)):
        char = cleaned[i]
        
        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
            
        if not in_string:
            if char == start_char:
                brace_count += 1
            elif char == end_char:
                brace_count -= 1
                if brace_count == 0:
                    json_str = cleaned[start_idx:i+1]
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Found JSON block but parsing failed: {e}\nBlock content:\n{json_str}")
                        
    raise ValueError("No matching closed JSON block could be successfully extracted from response.")

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
            if "choices" in res_data:
                return res_data["choices"][0]["message"]["content"]
            elif "content" in res_data:
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

# TF-IDF Retrieval Implementation
def tokenize(text):
    text = text.lower()
    # Replace hyphens/underscores/non-alphanumeric with spaces
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[-_]", " ", text)
    words = text.split()
    return [w for w in words if w not in STOPWORDS and len(w) > 1]

class TFIDFRetriever:
    def __init__(self, skills):
        self.skills = skills
        self.documents = []
        self.vocab = set()
        
        # Build document texts
        for s in skills:
            doc_text = " ".join([
                s["name"],
                s["description"],
                " ".join(s.get("triggers", []))
            ])
            tokens = tokenize(doc_text)
            self.documents.append(tokens)
            self.vocab.update(tokens)
            
        self.vocab = sorted(list(self.vocab))
        self.vocab_idx = {word: i for i, word in enumerate(self.vocab)}
        
        # Document frequencies
        self.df = {}
        for doc in self.documents:
            seen = set(doc)
            for w in seen:
                self.df[w] = self.df.get(w, 0) + 1
                
        # Inverse document frequencies
        self.N = len(skills)
        self.idf = {}
        for w in self.vocab:
            self.idf[w] = math.log(1.0 + (self.N / (1.0 + self.df.get(w, 0))))
            
        # Compute skill vectors
        self.skill_vectors = []
        for doc in self.documents:
            vec = self.vectorize(doc)
            self.skill_vectors.append(vec)

    def vectorize(self, tokens):
        tf = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
            
        vec = {}
        for t, count in tf.items():
            if t in self.vocab_idx:
                # Term Frequency normalized by length
                tf_val = count / len(tokens) if tokens else 0
                vec[self.vocab_idx[t]] = tf_val * self.idf[t]
        return vec

    def cosine_similarity(self, vec1, vec2):
        dot_product = 0.0
        # vec1 and vec2 are dictionaries representing sparse vectors
        for idx, val in vec1.items():
            if idx in vec2:
                dot_product += val * vec2[idx]
                
        norm1 = math.sqrt(sum(val**2 for val in vec1.values()))
        norm2 = math.sqrt(sum(val**2 for val in vec2.values()))
        
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def retrieve(self, query_text, top_k=10):
        query_tokens = tokenize(query_text)
        query_vec = self.vectorize(query_tokens)
        
        scores = []
        for i, skill_vec in enumerate(self.skill_vectors):
            score = self.cosine_similarity(query_vec, skill_vec)
            scores.append((score, self.skills[i]))
            
        scores.sort(key=lambda x: x[0], reverse=True)
        return scores[:top_k]

def run_sad_pipeline(user_query, env):
    print(f"[*] Starting SkillWeave SAD routing pipeline...")
    print(f"[*] Provider: {env.get('SKILLWEAVE_PROVIDER', 'lmstudio')} | Model: {env.get('SKILLWEAVE_MODEL', 'local-model')}")

    # Load paths
    index_path = env.get("SKILLWEAVE_SKILL_INDEX_PATH", ".agents/plugins/superpowers/skills/skill-index.json")
    dag_path = env.get("SKILLWEAVE_SKILL_DAG_PATH", ".agents/plugins/superpowers/skills/skill-dag.json")
    
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

    # Initialize TF-IDF retriever
    retriever = TFIDFRetriever(skill_index["skills"])

    # --- Phase 1: Task Decomposition ---
    print("\n[*] Phase 1: Task Decomposition (LLM)...")
    decomposition_prompt = f"""You are the SkillWeave Task Decomposer.
Your job is to break down the user's request into a sequential list of atomic, domain-specific engineering sub-tasks.
Avoid generic or compound steps. Keep steps clear, focused, and minimal.

User Query: "{user_query}"

Instructions:
1. Output ONLY a valid JSON list of strings representing the sub-tasks in sequential order.
2. Do NOT write any code, markdown, or conversational preambles.
3. Example output structure:
[
  "design the API schema",
  "write backend tests",
  "implement the auth middleware"
]

Output ONLY the JSON list:
"""
    
    decomp_res = call_llm(decomposition_prompt, env)
    try:
        subtasks = extract_json_block(decomp_res)
        if not isinstance(subtasks, list):
            raise ValueError("LLM response did not parse as a JSON list")
    except Exception as e:
        print(f"[-] Failed to parse initial decomposition: {e}. Raw response:\n{decomp_res}", file=sys.stderr)
        print("[*] Falling back to query as a single sub-task.")
        subtasks = [user_query]

    print(f"[+] Initial Decomposition complete. Sub-tasks generated:")
    for i, st in enumerate(subtasks):
        print(f"  {i+1}. {st}")

    # --- Phase 2: Iterative SAD Verification Loop ---
    print("\n[*] Phase 2: Iterative Skill Alignment Loop...")
    
    aligned_steps = []
    max_retries = 3
    retries = 0
    fully_aligned = False
    
    while retries <= max_retries and not fully_aligned:
        aligned_steps = []
        unaligned_subtasks = []
        
        for st in subtasks:
            # Retrieve top matching candidate skills
            matches = retriever.retrieve(st, top_k=3)
            best_match = matches[0] if matches else (0.0, None)
            
            score, skill = best_match
            # Strict threshold check (similarity >= 0.15)
            if score >= 0.15 and skill:
                aligned_steps.append({
                    "subtask": st,
                    "skill": skill["name"],
                    "score": score,
                    "rationale": f"Aligned via semantic search (similarity: {score:.3f})"
                })
            else:
                unaligned_subtasks.append(st)
                
        alignment_score = len(aligned_steps) / len(subtasks) if subtasks else 0.0
        print(f"[*] Loop iteration {retries + 1} | Alignment Score: {alignment_score:.2f} (Aligned: {len(aligned_steps)}/{len(subtasks)})")
        
        if alignment_score == 1.0:
            fully_aligned = True
            print("[+] All sub-tasks successfully aligned to expert skills!")
            break
            
        if retries == max_retries:
            print("[!] Maximum re-decomposition retries reached. Proceeding with partial alignment.")
            # Map unaligned steps to generic implementation skill
            for st in unaligned_subtasks:
                aligned_steps.append({
                    "subtask": st,
                    "skill": "executing-plans", # Default fallback process skill
                    "score": 0.0,
                    "rationale": "Fallback: No highly-aligned skill found"
                })
            break
            
        # Compile unique candidates for the unaligned tasks
        print(f"[-] Unaligned sub-tasks detected:")
        candidates_feedback = []
        for st in unaligned_subtasks:
            st_matches = retriever.retrieve(st, top_k=4)
            candidates_str = ", ".join([f"[{m[1]['name']}]" for m in st_matches if m[1]])
            print(f"  - \"{st}\" (Suggested skills: {candidates_str})")
            
            # Format detailed list for LLM context
            for score, sk in st_matches:
                if sk and sk not in candidates_feedback:
                    candidates_feedback.append(sk)
                    
        print("[*] Requesting re-decomposition from LLM with feedback...")
        
        feedback_prompt = f"""You are the SkillWeave SAD Alignment Optimizer.
We are decomposing the user query: "{user_query}"
Your initial sub-tasks were: {json.dumps(subtasks, indent=2)}

CRITICAL ERROR: The following sub-tasks could NOT be aligned with any available skills in our library:
{json.dumps(unaligned_subtasks, indent=2)}

Here is a list of candidate skills from our library that you MUST align to:
{json.dumps([{"name": sk["name"], "description": sk["description"], "triggers": sk["triggers"]} for sk in candidates_feedback], indent=2)}

Instructions:
1. Re-decompose or rephrase the unaligned sub-tasks so they map cleanly onto the triggers and descriptions of the candidate skills.
2. Return the COMPLETE, updated, sequential list of sub-tasks in JSON.
3. Output ONLY a valid JSON list of strings (no other text).

Updated Sub-tasks JSON:
"""
        
        decomp_res = call_llm(feedback_prompt, env)
        try:
            new_subtasks = extract_json_block(decomp_res)
            if isinstance(new_subtasks, list) and len(new_subtasks) > 0:
                subtasks = new_subtasks
                print(f"[+] Re-decomposition loaded for next iteration:")
                for i, st in enumerate(subtasks):
                    print(f"  {i+1}. {st}")
            else:
                print("[-] Received invalid JSON format from LLM feedback. Retrying with same tasks.")
        except Exception as e:
            print(f"[-] Failed to parse re-decomposition response: {e}.", file=sys.stderr)
            
        retries += 1

    # Print Final Alignment results
    print("\n[+] Final Skill Alignment:")
    for st_info in aligned_steps:
        print(f"  - \"{st_info['subtask']}\" -> [{st_info['skill']}] (score: {st_info['score']:.3f})")

    # --- Phase 3: Composition & DAG Ordering ---
    print("\n[*] Phase 3: Composition & DAG Ordering...")
    edges = skill_dag.get("edges", [])
    required_skills = list(set([step["skill"] for step in aligned_steps]))
    
    # Topological sort
    ordered_skills = []
    visited = set()
    temp_visited = set()

    def visit(node):
        if node in temp_visited:
            return  # Cycle detected
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
