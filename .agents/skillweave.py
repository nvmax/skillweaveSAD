#!/usr/bin/env python3
import os
import sys
import json
import re
import math
import urllib.request
import urllib.error

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

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
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(script_dir) == ".agents":
        workspace_root = os.path.dirname(script_dir)
        possible_paths = [
            os.path.join(script_dir, "skillweave.env"),
            os.path.join(workspace_root, ".env"),
            os.path.join(script_dir, "skillweave.env.example"),
            os.path.join(workspace_root, ".env.example")
        ]
    else:
        workspace_root = script_dir
        possible_paths = [
            os.path.join(workspace_root, ".agents", "skillweave.env"),
            os.path.join(workspace_root, ".env"),
            os.path.join(workspace_root, ".agents", "skillweave.env.example"),
            os.path.join(workspace_root, ".env.example")
        ]
        
    env_path = None
    for p in possible_paths:
        if os.path.exists(p):
            env_path = p
            break
            
    if env_path and os.path.exists(env_path):
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
    base_url = env.get("SKILLWEAVE_BASE_URL", "").strip()
    temp = float(env.get("SKILLWEAVE_TEMPERATURE", "0.1"))
    max_tokens = int(env.get("SKILLWEAVE_MAX_TOKENS", "4096"))

    headers = {"Content-Type": "application/json"}
    payload = {}

    if provider == "gemini":
        url = base_url if base_url else "https://generativelanguage.googleapis.com/v1beta/openai/v1"
        if not url.endswith("/chat/completions"):
            url = url.rstrip("/") + "/chat/completions"
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
        url = base_url if base_url else "https://api.anthropic.com"
        if not (url.endswith("/messages") or url.endswith("/messages/")):
            url = url.rstrip("/") + "/v1/messages"
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
            url = base_url if base_url else "https://api.openai.com/v1"
            headers["Authorization"] = f"Bearer {api_key}"
        elif provider == "lmstudio":
            url = base_url if base_url else "http://localhost:1234/v1"
        else: # ollama
            url = base_url if base_url else "http://localhost:11434/v1"
        
        if not url.endswith("/chat/completions"):
            url = url.rstrip("/") + "/chat/completions"
            
        if provider == "openai" or (provider == "ollama" and api_key):
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
        raise e

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

def dense_cosine_similarity(v1, v2):
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a**2 for a in v1))
    norm2 = math.sqrt(sum(b**2 for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot_product / (norm1 * norm2)

class SentenceTransformerRetriever:
    def __init__(self, skills):
        self.skills = skills
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.skill_texts = []
        for s in skills:
            doc_text = " ".join([
                s["name"],
                s["description"],
                " ".join(s.get("triggers", []))
            ])
            self.skill_texts.append(doc_text)
        # Encode all skill texts into embeddings
        self.skill_embeddings = self.model.encode(self.skill_texts, convert_to_numpy=True).tolist()

    def retrieve(self, query_text, top_k=10):
        query_emb = self.model.encode(query_text, convert_to_numpy=True).tolist()
        scores = []
        for i, skill_emb in enumerate(self.skill_embeddings):
            score = dense_cosine_similarity(query_emb, skill_emb)
            scores.append((score, self.skills[i]))
        scores.sort(key=lambda x: x[0], reverse=True)
        return scores[:top_k]

def compatibility(sa, sb, edges):
    # 1. I/O type coercion
    sa_outputs = set(sa.get("outputs", []))
    sb_depends = set(sb.get("depends_on", []))
    io_score = 0.0
    if sa_outputs or sb_depends:
        io_score = len(sa_outputs.intersection(sb_depends)) / max(1, len(sa_outputs.union(sb_depends)))
    
    # DAG edge score
    has_edge = any(edge["from"] == sa["name"] and edge["to"] == sb["name"] for edge in edges)
    has_reverse = any(edge["from"] == sb["name"] and edge["to"] == sa["name"] for edge in edges)
    if has_edge:
        io_score += 0.5
    if has_reverse:
        io_score -= 0.5

    # 2. Category Jaccard
    sa_cat = sa.get("category", "")
    sb_cat = sb.get("category", "")
    cat_jaccard = 1.0 if sa_cat and sb_cat and sa_cat == sb_cat else 0.0

    # 3. Keyword co-occurrence
    sa_triggers = sa.get("triggers", [])
    sb_triggers = sb.get("triggers", [])
    sa_tokens = set(tokenize(" ".join(sa_triggers)))
    sb_tokens = set(tokenize(" ".join(sb_triggers)))
    keyword_jaccard = 0.0
    if sa_tokens or sb_tokens:
        keyword_jaccard = len(sa_tokens.intersection(sb_tokens)) / max(1, len(sa_tokens.union(sb_tokens)))

    # Weighted sum
    w1, w2, w3 = 0.5, 0.25, 0.25
    return w1 * io_score + w2 * cat_jaccard + w3 * keyword_jaccard

def run_sad_pipeline(user_query, env):
    print(f"[*] Starting SkillWeave SAD routing pipeline...")
    print(f"[*] Provider: {env.get('SKILLWEAVE_PROVIDER', 'lmstudio')} | Model: {env.get('SKILLWEAVE_MODEL', 'local-model')}")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(script_dir) == ".agents":
        base_dir = os.path.dirname(script_dir)
    else:
        base_dir = script_dir
        
    index_path = env.get("SKILLWEAVE_SKILL_INDEX_PATH", ".agents/plugins/superpowers/skills/skill-index.json")
    dag_path = env.get("SKILLWEAVE_SKILL_DAG_PATH", ".agents/plugins/superpowers/skills/skill-dag.json")
        
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

    # Initialize retriever
    if SENTENCE_TRANSFORMERS_AVAILABLE:
        print("[*] Info: Using SentenceTransformer (all-MiniLM-L6-v2) for semantic retrieval.")
        retriever = SentenceTransformerRetriever(skill_index["skills"])
        similarity_threshold = 0.35
    else:
        print("[*] Info: sentence-transformers not installed. Falling back to TF-IDF retriever.")
        retriever = TFIDFRetriever(skill_index["skills"])
        similarity_threshold = 0.15

    # --- Phase 1 & 2: Iterative SAD Feedback Loop (Algorithm 1) ---
    print("\n[*] Phase 1 & 2: Iterative Skill-Aware Decomposition (SAD) Loop...")
    
    hint_set_skills = [] # Initially empty, H_0 = empty
    subtasks = []
    max_iterations = 4
    converged = False
    
    for iteration in range(1, max_iterations + 1):
        if not hint_set_skills:
            # Initial decomposition, no hints
            decomposition_prompt = f"""You are the SkillWeave Task Decomposer.
Your job is to break down the user's request into a sequential list of atomic engineering sub-tasks.
Avoid generic or compound steps. Keep steps clear, focused, and minimal. Do not mention any specific tools or skills.
Do not append, edit, or change any files with in .agents .cursor folders. 

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
        else:
            # Re-decomposition with hint set
            hints_json = json.dumps([
                {"name": s["name"], "description": s["description"], "triggers": s["triggers"]}
                for s in hint_set_skills
            ], indent=2)
            
            decomposition_prompt = f"""You are the SkillWeave Task Decomposer.
Your job is to break down the user's request into a sequential list of atomic engineering sub-tasks.
Avoid generic or compound steps. Keep steps clear, focused, and minimal.

User Query: "{user_query}"

To help you decompose this task, here is a "hint set" of candidate skills available in our library:
{hints_json}

Instructions:
1. Decompose the user query into sub-tasks such that each sub-task aligns closely with one of the candidate skills in the hint set.
2. Adjust the vocabulary and granularity of the sub-tasks to match the names, descriptions, and triggers of the candidate skills.
3. Output ONLY a valid JSON list of strings representing the sub-tasks in sequential order.
4. Do NOT write any code, markdown, or conversational preambles.

Output ONLY the JSON list:
"""
        
        try:
            decomp_res = call_llm(decomposition_prompt, env)
            new_subtasks = extract_json_block(decomp_res)
            if not isinstance(new_subtasks, list):
                raise ValueError("LLM response did not parse as a JSON list")
            subtasks = new_subtasks
        except Exception as e:
            print(f"[-] Loop iteration {iteration}: Failed to decompose or parse: {e}", file=sys.stderr)
            if iteration == 1:
                print("[*] Falling back to query as a single sub-task.")
                subtasks = [user_query]
        
        # Retrieve candidate skills for all sub-tasks
        new_hint_set_skills = []
        new_hint_names = set()
        for st in subtasks:
            st_matches = retriever.retrieve(st, top_k=3)
            for score, skill in st_matches:
                if skill and skill["name"] not in new_hint_names:
                    new_hint_names.add(skill["name"])
                    new_hint_set_skills.append(skill)
                    
        # Calculate Jaccard convergence
        prev_hint_names = {s["name"] for s in hint_set_skills}
        union_size = len(new_hint_names.union(prev_hint_names))
        intersection_size = len(new_hint_names.intersection(prev_hint_names))
        jaccard = intersection_size / union_size if union_size > 0 else 0.0
        
        print(f"[*] Iteration {iteration} | Sub-tasks: {len(subtasks)} | Hint Set Size: {len(new_hint_names)} | Hint Jaccard: {jaccard:.4f}")
        
        hint_set_skills = new_hint_set_skills
        
        if jaccard == 1.0:
            converged = True
            print(f"[+] Hint set stabilized (Jaccard = 1.0) after {iteration} iterations.")
            break
            
    if not converged:
        print("[!] Hint set did not fully stabilize, proceeding with last generated hints.")

    # --- Phase 3: Compatibility-Weighted Selection (Eq. 4) ---
    print("\n[*] Phase 3: Compatibility-Weighted Selection (Eq. 4)...")
    edges = skill_dag.get("edges", [])
    
    alpha = 0.5
    selected_steps = []
    preceding_skills = []
    
    for i, st in enumerate(subtasks):
        candidates = retriever.retrieve(st, top_k=3)
        best_skill = None
        best_score = -999.0
        best_sim = 0.0
        best_rationale = ""
        
        for sim_score, skill in candidates:
            if not skill:
                continue
            # Calculate compatibility
            comp_score = 0.0
            if i > 0:
                comp_score = sum(compatibility(prev, skill, edges) for prev in preceding_skills) / i
                
            combined_score = alpha * sim_score + (1.0 - alpha) * comp_score
            if combined_score > best_score:
                best_score = combined_score
                best_skill = skill
                best_sim = sim_score
                best_rationale = f"Combined score: {combined_score:.3f} (sim: {sim_score:.3f}, comp: {comp_score:.3f})"
                
        # Threshold check
        if best_skill and best_sim >= similarity_threshold:
            selected_steps.append({
                "subtask": st,
                "skill": best_skill["name"],
                "score": best_sim,
                "rationale": best_rationale
            })
            preceding_skills.append(best_skill)
        else:
            fallback_skill_name = "executing-plans"
            fallback_skill = next((s for s in skill_index["skills"] if s["name"] == fallback_skill_name), None)
            selected_steps.append({
                "subtask": st,
                "skill": fallback_skill_name,
                "score": 0.0,
                "rationale": f"Fallback: No candidate passed similarity threshold ({best_sim:.3f} < {similarity_threshold})"
            })
            if fallback_skill:
                preceding_skills.append(fallback_skill)

    # Print Final Alignment results
    print("\n[+] Final Skill Alignment:")
    for st_info in selected_steps:
        print(f"  - \"{st_info['subtask']}\" -> [{st_info['skill']}] ({st_info['rationale']})")

    # --- Phase 4: Composition & DAG Ordering ---
    print("\n[*] Phase 4: Composition & DAG Ordering...")
    required_skills = list(set([step["skill"] for step in selected_steps]))
    
    # Topological sort
    ordered_skills = []
    visited = set()
    temp_visited = set()

    def visit(node):
        if node in temp_visited:
            print(f"[!] Warning: Cycle detected in skill DAG at skill '{node}'!", file=sys.stderr)
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
    for idx, skill in enumerate(ordered_skills):
        skill_info = next((s for s in skill_index["skills"] if s["name"] == skill), None)
        path = skill_info["path"] if skill_info else "Unknown"
        print(f"  {idx+1}. [{skill}] (Source path: {path})")

    has_real_alignment = any(step["score"] > 0.0 for step in selected_steps)
    if not has_real_alignment:
        print("\n[-] Warning: No custom skills were aligned. Only fallback skills used.", file=sys.stderr)
        
    print("\n[+] Routing completed successfully! Provide this execution plan to your agent to load the respective skills.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python skillweave.py \"<user request>\"")
        sys.exit(1)
        
    query = sys.argv[1]
    env_config = load_env()
    run_sad_pipeline(query, env_config)
