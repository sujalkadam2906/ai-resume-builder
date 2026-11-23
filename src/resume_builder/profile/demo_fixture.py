"""Creates and manages the synthetic demo candidate fixture for multi-profile testing and isolation verification."""

import json
from pathlib import Path
from typing import Any, Dict
import yaml

from ..config import PROFILES_DIR, PROJECT_ROOT

DEMO_FIXTURE_DIR = PROJECT_ROOT / "tests" / "fixtures" / "profiles" / "demo_candidate"


def generate_demo_candidate_data() -> Dict[str, Any]:
    """Returns pure synthetic candidate data clearly labelled as a demo fixture."""
    return {
        "profile": {
            "_notice": "FICTIONAL DEMONSTRATION DATA — NOT A REAL CANDIDATE.",
            "personal_info": {
                "full_name": "Aarav Sharma (Demo Candidate)",
                "display_name": "AARAV SHARMA",
                "phone": "+91 9876543210",
                "email": "aarav.sharma.demo@example.com",
                "location": "Bengaluru, Karnataka, India",
                "open_to_relocate": True,
                "immediate_joiner": True,
            },
            "links": {
                "linkedin": {
                    "url": "https://www.linkedin.com/in/aarav-sharma-demo",
                    "display": "linkedin.com/in/aarav-sharma-demo",
                },
                "github": {
                    "url": "https://github.com/aaravsharma-demo",
                    "display": "github.com/aaravsharma-demo",
                },
                "portfolio": {
                    "url": "https://aarav-demo-portfolio.vercel.app",
                    "display": "aarav-demo-portfolio.vercel.app",
                },
            },
            "headlines": {
                "general": "Junior Frontend Developer | React & TypeScript Specialist",
                "primary": "Frontend Engineer | UI/UX & Responsive Web Design",
            },
            "summaries": {
                "master": (
                    "Frontend developer with 1 year of practical project experience building responsive, "
                    "accessible web applications using React 18, TypeScript, and Tailwind CSS. "
                    "Experienced in automated component testing with Vitest and REST API integration."
                ),
            },
            "education": [
                {
                    "degree": "B.E. in Computer Science and Engineering",
                    "institution": "Pune Institute of Computer Technology",
                    "duration": "2021–2025",
                    "start_year": 2021,
                    "end_year": 2025,
                    "cgpa": "8.50/10",
                    "score": "8.50",
                    "scale": "10",
                    "source": "demo_synthetic",
                }
            ],
            "technical_skills": {
                "languages": [
                    "JavaScript (ES6+)",
                    "TypeScript",
                    "HTML5",
                    "CSS3",
                    "Python (Basic)",
                ],
                "backend_and_java": [
                    "Node.js",
                    "Express.js",
                    "REST APIs",
                    "JSON Handling",
                ],
                "databases_and_sql": [
                    "PostgreSQL (Basic)",
                    "IndexedDB",
                    "localStorage",
                    "MongoDB",
                ],
                "cloud_devops_and_deployment": [
                    "Vercel",
                    "Netlify",
                    "GitHub Actions",
                    "Docker (Fundamentals)",
                ],
                "frontend": [
                    "React 18",
                    "TypeScript",
                    "Tailwind CSS",
                    "Redux Toolkit",
                    "Next.js",
                    "Responsive Web Design",
                    "Figma",
                ],
                "core_cs_and_ml": [
                    "Data Structures & Algorithms",
                    "OOP",
                    "DBMS Fundamentals",
                    "Web Accessibility (WAI-ARIA)",
                    "SDLC",
                ],
                "testing_and_tools": [
                    "Git",
                    "GitHub",
                    "Vitest",
                    "React Testing Library",
                    "Playwright",
                    "Vite",
                    "Webpack",
                    "Postman",
                ],
            },
            "leadership_and_experience": [
                {
                    "id": "gdsc_lead",
                    "role": "Frontend Track Lead",
                    "organization": "Google Developer Student Clubs (GDSC)",
                    "duration": "2023–2024",
                    "metrics": "Conducted 8 hands-on React workshops for 400+ attendees",
                    "description": "Led frontend web development workshops covering React, TypeScript, and modern responsive CSS for student developers.",
                    "bullets": [
                        "Conducted 8 hands-on React workshops for 400+ attendees, guiding students through production frontend architectures."
                    ],
                    "source": "demo_synthetic",
                }
            ],
            "professional_development": [
                {
                    "id": "meta_frontend_sim",
                    "title": "Meta Frontend Developer Professional Certificate Simulation",
                    "organization": "Meta / Coursera",
                    "date": "August 2024",
                    "bullets": [
                        "Completed comprehensive modules on responsive web UI design, accessibility, and client-side performance optimization.",
                        "Built accessible web components validating compliance with WCAG 2.1 AA contrast and screen-reader standards."
                    ],
                    "source": "demo_synthetic",
                }
            ],
            "achievements": [
                {
                    "id": "hackathon_first",
                    "title": "First Place — State Level Hackathon 2024",
                    "description": "Won 1st place among 120 teams for building an accessible telemedicine patient portal in React.",
                    "bullets": [
                        "Won 1st place among 120 teams for building an accessible telemedicine patient portal in React."
                    ],
                    "source": "demo_synthetic",
                }
            ],
            "research_publications": [],
            "certifications": [
                "Meta Certified Frontend Developer",
                "Responsive Web Design — freeCodeCamp",
                "TypeScript Fundamentals — ExecuteProgram",
            ],
        },
        "projects": [
            {
                "id": "cloud_canvas_ui",
                "title": "CloudCanvas UI Component Library",
                "subtitle": "React 18 · TypeScript · Tailwind CSS · Storybook · Vitest",
                "is_fixed_project": False,
                "fixed_position": None,
                "categories": ["Frontend", "React", "TypeScript", "Design Systems"],
                "skills": ["React 18", "TypeScript", "Tailwind CSS", "Storybook", "Vitest", "React Testing Library"],
                "links": [{"label": "GitHub", "url": "https://github.com/aaravsharma-demo/cloudcanvas-ui"}],
                "bullets": [
                    "Engineered an accessible React component library comprising 24 reusable UI elements with zero external CSS dependencies.",
                    "Achieved 95% unit test coverage using Vitest and React Testing Library; integrated automated Storybook visual regression checks."
                ],
                "metrics": ["24 reusable UI elements", "95% unit test coverage"],
                "evidence_source": "demo_synthetic",
                "verification_status": "verified"
            },
            {
                "id": "crypto_pulse_dashboard",
                "title": "CryptoPulse Real-Time Financial Dashboard",
                "subtitle": "React 18 · TypeScript · WebSocket · Chart.js · Tailwind CSS",
                "is_fixed_project": False,
                "fixed_position": None,
                "categories": ["Frontend", "React", "WebSockets", "Data Visualization"],
                "skills": ["React 18", "TypeScript", "WebSocket", "Chart.js", "Tailwind CSS", "IndexedDB"],
                "links": [{"label": "GitHub", "url": "https://github.com/aaravsharma-demo/cryptopulse-dashboard"}],
                "bullets": [
                    "Architected a responsive dashboard consuming WebSocket feeds to visualize real-time cryptocurrency price movements with sub-100ms render latency.",
                    "Implemented client-side caching with IndexedDB to support offline viewing of historical market trends across 50+ token pairs."
                ],
                "metrics": ["sub-100ms render latency", "50+ token pairs"],
                "evidence_source": "demo_synthetic",
                "verification_status": "verified"
            },
            {
                "id": "form_forge_engine",
                "title": "FormForge Accessible Forms Engine",
                "subtitle": "React · TypeScript · React Hook Form · Zod · WAI-ARIA",
                "is_fixed_project": False,
                "fixed_position": None,
                "categories": ["Frontend", "Forms", "Accessibility", "TypeScript"],
                "skills": ["React", "TypeScript", "React Hook Form", "Zod", "WAI-ARIA", "Accessibility"],
                "links": [{"label": "GitHub", "url": "https://github.com/aaravsharma-demo/formforge-engine"}],
                "bullets": [
                    "Built a schema-driven dynamic form engine with runtime Zod validation and full WAI-ARIA screen-reader compliance.",
                    "Reduced form completion drop-off by 35% through real-time field validation, accessible error announcements, and auto-save capabilities."
                ],
                "metrics": ["35% reduction in drop-off"],
                "evidence_source": "demo_synthetic",
                "verification_status": "verified"
            },
            {
                "id": "portfolio_builder_spa",
                "title": "PortfolioForge Web Application",
                "subtitle": "Next.js · TypeScript · Tailwind CSS · Vercel",
                "is_fixed_project": False,
                "fixed_position": None,
                "categories": ["Frontend", "Next.js", "Static Generation"],
                "skills": ["Next.js", "TypeScript", "Tailwind CSS", "Markdown", "Vercel"],
                "links": [{"label": "GitHub", "url": "https://github.com/aaravsharma-demo/portfolio-forge"}],
                "bullets": [
                    "Developed an interactive portfolio generator enabling software engineers to export responsive single-page portfolio websites.",
                    "Integrated Markdown parsing and automated GitHub API repository synchronization with instantaneous client-side preview rendering."
                ],
                "metrics": ["Instantaneous client preview"],
                "evidence_source": "demo_synthetic",
                "verification_status": "verified"
            }
        ],
        "config": {
            "profile_id": "demo_candidate",
            "display_name": "Aarav Sharma (Demo)",
            "is_synthetic": True,
            "headline_rule": {
                "mode": "permanent",
                "permanent_headline": "Junior Frontend Developer | React & TypeScript Specialist",
            },
            "summary_rule": {
                "mode": "permanent",
                "permanent_summary": (
                    "Frontend developer with 1 year of practical project experience building responsive, "
                    "accessible web applications using React 18, TypeScript, and Tailwind CSS. "
                    "Experienced in automated component testing with Vitest and REST API integration."
                ),
            },
            "prohibited_terms": [],
            "project_selection": {
                "target_count": 4,
                "has_fixed_project": False,
                "fixed_project": None,
                "weights": {
                    "required_skills_coverage": 0.45,
                    "responsibilities_alignment": 0.25,
                    "tech_stack_similarity": 0.20,
                    "domain_relevance": 0.10,
                },
            },
            "sections_order": [
                "header",
                "summary",
                "technical_skills",
                "projects",
                "professional_development",
                "education",
                "leadership_and_achievements",
                "certifications",
            ],
            "theme": "editorial_teal_copper",
        }
    }


def setup_demo_candidate_profile(dest_dir: Path) -> None:
    """Writes the demo candidate files to the specified directory and registers the profile."""
    from datetime import datetime
    dest_dir.mkdir(parents=True, exist_ok=True)
    for sub in ["source_resumes", "backups", "audit"]:
        (dest_dir / sub).mkdir(parents=True, exist_ok=True)

    data = generate_demo_candidate_data()

    with open(dest_dir / "master_profile.json", "w", encoding="utf-8") as f:
        json.dump(data["profile"], f, indent=2)

    with open(dest_dir / "projects.json", "w", encoding="utf-8") as f:
        json.dump(data["projects"], f, indent=2)

    with open(dest_dir / "profile_config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(data["config"], f, sort_keys=False, default_flow_style=False)

    # Register in registry.json if dest_dir is under PROFILES_DIR
    registry_file = PROFILES_DIR / "registry.json"
    registry_data: Dict[str, Any] = {"profiles": {}}
    if registry_file.exists():
        try:
            with open(registry_file, "r", encoding="utf-8") as f:
                registry_data = json.load(f)
        except Exception:
            registry_data = {"profiles": {}}

    if "demo_candidate" not in registry_data.get("profiles", {}):
        registry_data.setdefault("profiles", {})["demo_candidate"] = {
            "profile_id": "demo_candidate",
            "candidate_display_name": "Aarav Sharma (Demo Candidate)",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "source_status": "synthetic_fixture",
            "is_active": True,
            "schema_version": "2.0.0",
        }
        with open(registry_file, "w", encoding="utf-8") as f:
            json.dump(registry_data, f, indent=2)
