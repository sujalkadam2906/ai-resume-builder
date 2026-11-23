"""Technical keyword definitions, synonym mapping, and technical terminology rules."""

import re
from typing import Dict, List, Optional, Set, Tuple

# Canonical mapping for skills and synonyms
CANONICAL_SKILL_MAP: Dict[str, str] = {
    "java": "Java",
    "core java": "Java",
    "java 8": "Java 8",
    "spring": "Spring Boot",
    "spring boot": "Spring Boot",
    "springboot": "Spring Boot",
    "spring mvc": "Spring MVC",
    "spring data jpa": "Spring Data JPA",
    "jpa": "Spring Data JPA",
    "hibernate": "Hibernate",
    "rest": "REST APIs",
    "rest api": "REST APIs",
    "rest apis": "REST APIs",
    "restful": "REST APIs",
    "sql": "SQL",
    "mysql": "MySQL",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "es6": "JavaScript (ES6+)",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "react": "React 18",
    "reactjs": "React 18",
    "react.js": "React 18",
    "react js": "React 18",
    "react 18": "React 18",
    "html": "HTML5",
    "html5": "HTML5",
    "css": "CSS3",
    "css3": "CSS3",
    "css modules": "CSS Modules",
    "vite": "Vite",
    "indexeddb": "IndexedDB",
    "localstorage": "localStorage",
    "python": "Python",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "svm": "SVM",
    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "git": "Git",
    "github": "GitHub",
    "maven": "Maven",
    "junit": "JUnit 5",
    "junit 5": "JUnit 5",
    "pytest": "Pytest",
    "playwright": "Playwright",
    "reportlab": "ReportLab",
    "vitest": "Vitest",
    "react testing library": "React Testing Library",
    "oop": "OOP",
    "object oriented programming": "OOP",
    "dsa": "Data Structures & Algorithms",
    "data structures": "Data Structures & Algorithms",
    "algorithms": "Data Structures & Algorithms",
    "dbms": "DBMS",
    "operating systems": "OS",
    "computer networks": "Computer Networks",
    "sdlc": "SDLC",
    "figma": "Figma",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "websocket": "WebSockets",
    "websockets": "WebSockets",
    "gemini api": "Gemini API",
    "automation": "Workflow Automation",
    "iam": "Identity & Access Management (IAM)",
    "cybersecurity": "Cybersecurity",
    # External / Cloud / Unsupported skills for accurate recognition
    "aws": "AWS",
    "cloud": "Cloud Architecture",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "golang": "Go",
    "c++": "C++",
    "angular": "Angular",
    "vue": "Vue",
    "mongodb": "MongoDB",
}

# Technical keywords categorized
KNOWN_LANGUAGES = {"Java", "Python", "SQL", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", "PHP", "Ruby", "Kotlin", "Swift"}
KNOWN_FRAMEWORKS = {"Spring Boot", "Spring MVC", "Spring Data JPA", "Hibernate", "React 18", "Vue", "Angular", "Next.js", "Django", "Flask", "FastAPI", "Express"}
KNOWN_DATABASES = {"MySQL", "PostgreSQL", "MongoDB", "Oracle", "Redis", "SQLite", "DynamoDB", "Cassandra"}
KNOWN_TOOLS = {"Git", "GitHub", "Maven", "Gradle", "Docker", "Kubernetes", "JUnit 5", "Pytest", "Playwright", "ReportLab", "Vitest", "Vite", "Linux", "AWS", "Azure", "GCP", "Postman", "Figma", "Jira"}


def normalize_term(term: str) -> str:
    """Normalize a keyword to lowercase alphanumeric."""
    return re.sub(r"[^a-z0-9+#]", "", term.lower())


def canonicalize_skill(skill: str) -> str:
    """Map skill or synonym to its canonical form if known."""
    norm = skill.strip().lower()
    if norm in CANONICAL_SKILL_MAP:
        return CANONICAL_SKILL_MAP[norm]
    # Check without dots or dashes
    cleaned = re.sub(r"[\.\-_]", " ", norm).strip()
    if cleaned in CANONICAL_SKILL_MAP:
        return CANONICAL_SKILL_MAP[cleaned]
    # Also check alphanumeric
    alphanumeric = normalize_term(norm)
    for k, v in CANONICAL_SKILL_MAP.items():
        if normalize_term(k) == alphanumeric:
            return v
    return skill.strip()


def extract_keywords_from_text(text: str) -> Set[str]:
    """Extract recognized technical keywords from raw text."""
    found = set()
    text_lower = f" {text.lower()} "

    for synonym, canonical in CANONICAL_SKILL_MAP.items():
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(synonym) + r"(?![a-zA-Z0-9])"
        if re.search(pattern, text_lower):
            found.add(canonical)

    return found
