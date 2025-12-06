import re
from typing import Dict, List, Set
from collections import defaultdict


SKILL_TAXONOMY: Dict[str, Set[str]] = {
    "python": {"python", "py", "python3", "питон", "пайтон"},
    "javascript": {"javascript", "js", "es6", "es2015", "ecmascript", "джаваскрипт"},
    "typescript": {"typescript", "ts", "тайпскрипт"},
    "java": {"java", "джава"},
    "go": {"go", "golang", "го"},
    "rust": {"rust", "раст"},
    "c++": {"c++", "cpp", "cplusplus", "си++"},
    "c#": {"c#", "csharp", "си шарп"},
    "ruby": {"ruby", "руби"},
    "php": {"php", "пхп"},
    "kotlin": {"kotlin", "котлин"},
    "swift": {"swift", "свифт"},
    "react": {"react", "reactjs", "react.js", "реакт"},
    "vue": {"vue", "vuejs", "vue.js", "вью"},
    "angular": {"angular", "angularjs", "ангуляр"},
    "django": {"django", "джанго"},
    "flask": {"flask", "фласк"},
    "fastapi": {"fastapi", "fast-api", "фастапи"},
    "spring": {"spring", "spring boot", "springboot"},
    "node": {"node", "nodejs", "node.js", "нода"},
    "express": {"express", "expressjs", "express.js"},
    "postgresql": {"postgresql", "postgres", "pg", "постгрес", "постгресql"},
    "mysql": {"mysql", "май sql", "mysql"},
    "mongodb": {"mongodb", "mongo", "монго"},
    "redis": {"redis", "редис"},
    "elasticsearch": {"elasticsearch", "elastic", "эластик"},
    "docker": {"docker", "докер"},
    "kubernetes": {"kubernetes", "k8s", "кубер", "кубернетес"},
    "aws": {"aws", "amazon web services", "амазон"},
    "gcp": {"gcp", "google cloud", "гугл клауд"},
    "azure": {"azure", "азур", "азуре"},
    "terraform": {"terraform", "терраформ"},
    "ansible": {"ansible", "ансибл"},
    "jenkins": {"jenkins", "дженкинс"},
    "gitlab": {"gitlab", "gitlab ci", "гитлаб"},
    "github": {"github", "github actions", "гитхаб"},
    "pytorch": {"pytorch", "torch", "пайторч"},
    "tensorflow": {"tensorflow", "tf", "тензорфлоу"},
    "scikit-learn": {"scikit-learn", "sklearn", "сайкит"},
    "pandas": {"pandas", "пандас"},
    "numpy": {"numpy", "нампи"},
    "pytest": {"pytest", "py.test"},
    "jest": {"jest", "джест"},
    "selenium": {"selenium", "селениум"},
    "git": {"git", "гит"},
    "linux": {"linux", "линукс", "unix"},
    "rest": {"rest", "restful", "rest api", "рест"},
    "graphql": {"graphql", "graph ql", "графкуэл"},
    "microservices": {"microservices", "микросервисы"},
    "agile": {"agile", "scrum", "аджайл"},
}

_SYNONYM_TO_CANONICAL: Dict[str, str] = {}
for canonical, synonyms in SKILL_TAXONOMY.items():
    for syn in synonyms:
        _SYNONYM_TO_CANONICAL[syn.lower()] = canonical

CURRENCY_RATES: Dict[str, float] = {
    "RUR": 1.0,
    "RUB": 1.0,
    "₽": 1.0,
    "USD": 95.0,
    "EUR": 103.0,
    "KZT": 0.21,
    "BYR": 29.5,
    "UAH": 2.6,
    "AZN": 56.0,
    "GEL": 35.0,
    "UZS": 0.0075,
}


def normalize_skill(skill: str) -> str:
    if not skill:
        return ""
    cleaned = re.sub(r'<[^>]+>', '', skill)
    cleaned = cleaned.replace('…', ' ')
    cleaned = re.sub(r'\s+', ' ', cleaned).strip().lower()
    cleaned = re.sub(r'[^\w\s\+\#\-\.]', '', cleaned)
    if not cleaned:
        return ""
    canonical = _SYNONYM_TO_CANONICAL.get(cleaned)
    if canonical:
        return canonical
    return cleaned


def normalize_skills_batch(skills: List[str]) -> List[str]:
    normalized = set()
    for skill in skills:
        norm = normalize_skill(skill)
        if norm:
            normalized.add(norm)
    return sorted(list(normalized))


def convert_salary_to_rub(amount: float, currency: str) -> float:
    if not currency:
        return amount
    rate = CURRENCY_RATES.get(currency.upper(), 1.0)
    return amount * rate


def categorize_skill(skill: str) -> str:
    backend_langs = {"python", "java", "go", "rust", "c++", "c#", "ruby", "php", "kotlin"}
    frontend_langs = {"javascript", "typescript"}
    frameworks_backend = {"django", "flask", "fastapi", "spring", "node", "express"}
    frameworks_frontend = {"react", "vue", "angular"}
    databases = {"postgresql", "mysql", "mongodb", "redis", "elasticsearch"}
    ml_tools = {"pytorch", "tensorflow", "scikit-learn", "pandas", "numpy"}
    devops = {"docker", "kubernetes", "aws", "gcp", "azure", "terraform", "ansible", "jenkins", "gitlab", "github"}

    skill_lower = skill.lower()
    if skill_lower in backend_langs or skill_lower in frameworks_backend:
        return "backend"
    if skill_lower in frontend_langs or skill_lower in frameworks_frontend:
        return "frontend"
    if skill_lower in ml_tools:
        return "ml"
    if skill_lower in databases:
        return "database"
    if skill_lower in devops:
        return "devops"
    return "other"


def extract_seniority_from_text(text: str) -> str:
    text_lower = text.lower()
    if any(word in text_lower for word in ["senior", "lead", "principal", "architect", "старший"]):
        return "senior"
    if any(word in text_lower for word in ["middle", "средний"]):
        return "middle"
    if any(word in text_lower for word in ["junior", "младший", "стажер", "intern"]):
        return "junior"
    return "unknown"


def calculate_skill_similarity(skills1: Set[str], skills2: Set[str]) -> float:
    if not skills1 or not skills2:
        return 0.0
    intersection = len(skills1 & skills2)
    union = len(skills1 | skills2)
    return intersection / union if union > 0 else 0.0


def group_skills_by_category(skills: List[str]) -> Dict[str, List[str]]:
    grouped = defaultdict(list)
    for skill in skills:
        category = categorize_skill(skill)
        grouped[category].append(skill)
    return dict(grouped)
