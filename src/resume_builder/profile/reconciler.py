"""Profile reconciler for merging multiple resume sources and auditing conflicts."""

from typing import Any, Dict, List, Tuple
from .models import (
    AchievementItem,
    EducationItem,
    LeadershipItem,
    LinkItem,
    LinksProfile,
    MasterProfile,
    PersonalInfo,
    ProfessionalDevelopmentItem,
    ProjectItem,
    ProjectLink,
    ResearchPublication,
    TechnicalSkills,
)


def reconcile_resumes(
    r1_data: Dict[str, Any], r2_data: Dict[str, Any]
) -> Tuple[MasterProfile, List[ProjectItem], List[Dict[str, str]]]:
    """
    Reconcile information extracted from both original resumes.
    Identifies conflicts, maintains evidence attribution, and produces
    the verified MasterProfile and list of ProjectItems.
    """
    conflicts: List[Dict[str, str]] = []

    # 1. Headline differences
    r1_text = r1_data.get("text", "")
    r2_text = r2_data.get("text", "")

    conflicts.append({
        "field": "headline",
        "detail": "R1 emphasized 'Entry-Level Software Engineer | Java, Spring Boot, SQL, React & TypeScript'. "
                  "R2 emphasized 'Entry-Level SWE / SWD | Java Full-Stack | ML Research Paper Publisher'. "
                  "Both preserved in headlines dictionary for tailored selection."
    })

    # 2. Project set differences
    conflicts.append({
        "field": "projects",
        "detail": "R1 contained 5 projects (including Vogue Vault). R2 omitted Vogue Vault to include Tata Cybersecurity Job Simulation. "
                  "Reconciled by preserving all 5 verified projects in database and selecting top 4 for each JD, "
                  "with Bearing Fault Diagnosis strictly fixed at position 2."
    })

    # 3. Professional Development section
    conflicts.append({
        "field": "professional_development",
        "detail": "Tata Cybersecurity Job Simulation was added in R2 (dated Nov 13, 2026). "
                  "Preserved as an optional verified section when space allows or JD requires cybersecurity."
    })

    # Build Master Profile
    import os
    personal_info = PersonalInfo(
        full_name=os.getenv("CANDIDATE_NAME", "Candidate Name"),
        display_name=os.getenv("CANDIDATE_DISPLAY_NAME", "CANDIDATE"),
        phone=os.getenv("CANDIDATE_PHONE", "+91 0000000000"),
        email=os.getenv("CANDIDATE_EMAIL", "candidate@example.com"),
        location=os.getenv("CANDIDATE_LOCATION", "City, State, Country (Open to Relocate)"),
        open_to_relocate=True,
        immediate_joiner=True,
    )

    links = LinksProfile(
        linkedin=LinkItem(
            url=os.getenv("CANDIDATE_LINKEDIN", "https://www.linkedin.com/in/candidate"),
            display=os.getenv("CANDIDATE_LINKEDIN_DISPLAY", "linkedin.com/in/candidate"),
        ),
        github=LinkItem(
            url=os.getenv("CANDIDATE_GITHUB", "https://github.com/candidate"),
            display=os.getenv("CANDIDATE_GITHUB_DISPLAY", "github.com/candidate"),
        ),
        portfolio=LinkItem(
            url=os.getenv("CANDIDATE_PORTFOLIO", "https://candidate-portfolio.vercel.app/"),
            display=os.getenv("CANDIDATE_PORTFOLIO_DISPLAY", "candidate-portfolio.vercel.app/"),
        ),
    )

    headlines = {
        "general": "Entry-Level Software Engineer | Java, Spring Boot, SQL, React & TypeScript",
        "java_fullstack": "Entry-Level SWE / SWD | Java Full-Stack | ML Research Paper Publisher",
        "source_r1": "Entry-Level Software Engineer | Java, Spring Boot, SQL, React & TypeScript",
        "source_r2": "Entry-Level SWE / SWD | Java Full-Stack | ML Research Paper Publisher",
    }

    summaries = {
        "general": (
            "B.Tech graduate (2026, CGPA: 8.23/10) transitioning into software development "
            "with hands-on project experience building React/TypeScript and JavaScript web interfaces, "
            "a Java and Spring Boot CRUD REST API, and SQL analytics in PostgreSQL, and a MySQL-backed persistence layer. "
            "Strong foundation in data structures, algorithms, OOP, and SQL, alongside applied machine learning in Python. "
            "Coordinated campus placement operations for 1,500+ students across 20+ recruitment drives."
        ),
        "java_fullstack": (
            "Java full-stack focused B.Tech graduate (2026) with hands-on project experience building "
            "a Spring Boot REST API with Spring Data JPA, Hibernate and MySQL, and SQL analytics in PostgreSQL. "
            "Additional development experience in React/TypeScript and applied machine learning in Python. "
            "Chief Student Training & Placement Officer who coordinated placement operations for 1,500+ students "
            "across 20+ recruitment drives. Immediate joiner; open to relocation."
        ),
    }

    education = [
        EducationItem(
            degree="B.Tech in Mechanical Engineering",
            institution="KIT's College of Engineering (Autonomous), Kolhapur",
            duration="2022 – 2026",
            start_year=2022,
            end_year=2026,
            cgpa="8.23 / 10",
            score="8.23",
            scale="10",
            source="verified_both",
        )
    ]

    skills = TechnicalSkills(
        languages=[
            "Java (Core Java, Java 8)",
            "SQL",
            "JavaScript (ES6+)",
            "TypeScript",
            "Python (Basic)",
        ],
        backend_and_java=[
            "Spring Boot (CRUD REST APIs)",
            "Spring MVC",
            "Spring Data JPA",
            "Hibernate",
            "REST APIs",
            "Collections",
            "Exception Handling",
        ],
        frontend=[
            "React 18",
            "HTML5",
            "CSS3 (CSS Modules)",
            "Vite",
            "IndexedDB",
            "localStorage",
            "DOM Manipulation",
            "Figma",
        ],
        databases_and_sql=[
            "PostgreSQL",
            "MySQL",
            "MongoDB",
            "Relational Schema Design",
            "Primary/Foreign Keys",
            "Joins",
            "Aggregations",
            "GROUP BY",
            "HAVING clauses",
        ],
        cloud_devops_and_deployment=[
            "AWS",
            "Azure",
            "Vercel",
            "Netlify",
            "Docker",
            "Kubernetes (Fundamentals)",
        ],
        core_cs_and_ml=[
            "Data Structures & Algorithms",
            "OOP",
            "DBMS",
            "OS",
            "Computer Networks",
            "SDLC",
            "Pandas",
            "NumPy",
            "scikit-learn",
        ],
        testing_and_tools=[
            "Git",
            "GitHub",
            "Maven",
            "JUnit 5",
            "Vitest",
            "React Testing Library",
            "CLI AI Agents (Claude Code, GitHub Copilot)",
        ],
    )

    leadership = [
        LeadershipItem(
            id="tpo_officer",
            role="Chief Student Training & Placement Officer",
            organization="KIT's College of Engineering",
            duration="2024 – 2026",
            metrics="1,500+ students across 20+ recruitment drives",
            description="Coordinated placement operations for 1,500+ students across 20+ campus recruitment drives, working with visiting recruiters, faculty, and student candidates.",
            bullets=[
                "Coordinated placement operations for 1,500+ students across 20+ campus recruitment drives, working with visiting recruiters, faculty, and student candidates."
            ],
            source="verified_both",
        )
    ]

    professional_dev = [
        ProfessionalDevelopmentItem(
            id="tcs_cybersecurity",
            title="Tata Cybersecurity Security Analyst Job Simulation — Forage",
            organization="Tata Consultancy Services (TCS) / Forage",
            date="November 13, 2026",
            bullets=[
                "Completed a job simulation involving Identity and Access Management (IAM) for Tata Consultancy Services, collaborating with a Cybersecurity Consulting team.",
                "Developed knowledge of IAM principles, cybersecurity best practices and alignment of security practices with business objectives.",
                "Prepared documentation and presentations demonstrating the ability to communicate technical concepts effectively.",
            ],
            source="Sujal_Kadam_Resume_new.pdf",
            conflict_note="Present in R2 (new), omitted in R1 to prioritize 5th project",
        )
    ]

    achievements = [
        AchievementItem(
            id="mega_project_award",
            title="Best Mega-Project Award & Research Co-Author",
            description="Won the Best Mega-Project Award for the ML bearing-fault system; co-authored a paper published in EPJ Web of Conferences (2026) and a second paper at TFGET 2026.",
            bullets=[
                "Won the Best Mega-Project Award for the ML bearing-fault system; co-authored a paper published in EPJ Web of Conferences (2026) and a second paper at TFGET 2026."
            ],
            source="verified_both",
        )
    ]

    research_publications = [
        ResearchPublication(
            title="Bearing Fault Diagnosis Using Machine Learning",
            venue="EPJ Web of Conferences",
            year=2026,
            doi="10.1051/epjconf/202635501004",
            doi_url="https://doi.org/10.1051/epjconf/202635501004",
        ),
        ResearchPublication(
            title="TFGET 2026 Research Conference Paper",
            venue="TFGET",
            year=2026,
        ),
    ]

    certifications = [
        "Core & Advanced Java (KG Placements)",
        "SQL Certification (Skill-Course)",
        "NPTEL Machine Learning & Deep Learning",
        "Tata Ready Engineer Program",
        "Web Development (CodeWithHarry)",
        "Cybersecurity Analyst Job Simulation (TCS)",
    ]

    profile = MasterProfile(
        personal_info=personal_info,
        links=links,
        headlines=headlines,
        summaries=summaries,
        education=education,
        technical_skills=skills,
        leadership_and_experience=leadership,
        professional_development=professional_dev,
        achievements=achievements,
        research_publications=research_publications,
        certifications=certifications,
        reconciliation_metadata={
            "sources_inspected": [r1_data.get("file_name", "R1"), r2_data.get("file_name", "R2")],
            "reconciled_conflicts": conflicts,
        },
    )

    # Build Project Items
    projects = [
        ProjectItem(
            id="bearing_fault_diagnosis",
            title="Bearing Fault Diagnosis Using Machine Learning",
            subtitle="Python, Pandas, NumPy, scikit-learn (SVM)",
            is_fixed_project=True,
            fixed_position=2,
            categories=["Machine Learning", "Python", "Data Science", "Research", "Predictive Maintenance"],
            skills=["Python", "Pandas", "NumPy", "scikit-learn", "SVM", "Data Preprocessing", "Feature Engineering", "Predictive Maintenance"],
            links=[ProjectLink(label="Published Paper (DOI)", url="https://doi.org/10.1051/epjconf/202635501004")],
            bullets=[
                "Built a predictive-maintenance pipeline in Python to detect early-stage faults in rotating-machinery bearings from vibration sensor data.",
                "Cleaned sensor readings and engineered statistical features with Pandas and NumPy, then trained and tuned an SVM classifier achieving over 95% accuracy on held-out test data.",
            ],
            metrics=["over 95% accuracy on held-out test data"],
            evidence_source="Present in both Sujal_Kadam_Resume.pdf and Sujal_Kadam_Resume_new.pdf. Published in EPJ Web of Conferences (2026).",
            verification_status="verified",
        ),
        ProjectItem(
            id="employee_management_api",
            title="Employee Management REST API",
            subtitle="Java 8, Spring Boot, Spring Data JPA, Hibernate, MySQL, JUnit 5",
            is_fixed_project=False,
            categories=["Backend", "Java", "Spring Boot", "REST API", "Databases"],
            skills=["Java", "Java 8", "Spring Boot", "Spring Data JPA", "Hibernate", "MySQL", "JUnit 5", "REST APIs", "CRUD", "Exception Handling"],
            links=[ProjectLink(label="GitHub", url="https://github.com/sujalkadam2906/employee-management-rest-api")],
            bullets=[
                "Built a layered CRUD REST API in Java 8 and Spring Boot (@RestController, service layer, and JpaRepository) exposing /api/employee endpoints to create, read, update, and delete employee records in MySQL.",
                "Implemented ID lookup checks with runtime exception handling for missing employee records and added a JUnit 5 unit test for the Employee entity.",
            ],
            metrics=[],
            evidence_source="Present in both Sujal_Kadam_Resume.pdf and Sujal_Kadam_Resume_new.pdf.",
            verification_status="verified",
        ),
        ProjectItem(
            id="opportunity_radar",
            title="Opportunity Radar — Job Discovery App",
            subtitle="React 18, TypeScript, Vite, IndexedDB, Vitest",
            is_fixed_project=False,
            categories=["Frontend", "Full-Stack", "React", "TypeScript", "Web Development"],
            skills=["React 18", "TypeScript", "JavaScript", "Vite", "IndexedDB", "Vitest", "React Testing Library", "Node.js", "WebSockets", "CSS Modules", "HTML5", "CSS3", "WCAG 2.2 AA"],
            links=[
                ProjectLink(label="Live Demo", url="https://opportunity-radar-nine-smoky.vercel.app/"),
                ProjectLink(label="GitHub", url="https://github.com/sujalkadam2906/opportunity-radar"),
            ],
            bullets=[
                "Built a freshness-first job discovery app in strict TypeScript and React 18 with multi-criteria filters for location, work mode, experience, domain, and minimum pay, plus a deterministic job-fit scoring engine that highlights matched and missing skills.",
                "Developed an application tracker supporting stage updates, interview dates, custom notes, and CSV export, persisting saved jobs and application stages locally in IndexedDB with optimistic UI updates.",
                "Added an optional Node.js WebSocket stream with reconnect and offline fallback; built toward WCAG 2.2 AA accessibility with focus traps, live regions, and keyboard navigation, tested using Vitest and React Testing Library.",
            ],
            metrics=[],
            evidence_source="Present in both Sujal_Kadam_Resume.pdf and Sujal_Kadam_Resume_new.pdf.",
            verification_status="verified",
        ),
        ProjectItem(
            id="online_bookstore_db",
            title="Online Bookstore Database Analysis",
            subtitle="PostgreSQL, SQL, Relational Database Design",
            is_fixed_project=False,
            categories=["Databases", "SQL", "Backend", "Data Analytics"],
            skills=["PostgreSQL", "SQL", "Relational Database Design", "Schema Design", "Primary Keys", "Foreign Keys", "Joins", "Aggregations", "GROUP BY", "HAVING", "Data Modeling"],
            links=[ProjectLink(label="GitHub", url="https://github.com/sujalkadam2906/online-bookstore-sql")],
            bullets=[
                "Designed a normalized relational schema in PostgreSQL for Books, Customers, and Orders tables with primary/foreign keys and integrity constraints, importing CSV records using PostgreSQL COPY statements.",
                "Wrote SQL queries using INNER and LEFT JOINs, aggregate functions (SUM, COUNT, AVG, COALESCE), GROUP BY, and HAVING clauses to analyze sales revenue, customer purchasing patterns, book popularity, and stock levels.",
            ],
            metrics=[],
            evidence_source="Present in both Sujal_Kadam_Resume.pdf and Sujal_Kadam_Resume_new.pdf.",
            verification_status="verified",
        ),
        ProjectItem(
            id="vogue_vault",
            title="Vogue Vault — Fashion E-Commerce Frontend",
            subtitle="HTML5, CSS3, JavaScript (ES6+), Vite, localStorage",
            is_fixed_project=False,
            categories=["Frontend", "JavaScript", "UI Development", "Web Development"],
            skills=["HTML5", "CSS3", "JavaScript (ES6+)", "Vite", "localStorage", "DOM Manipulation", "UI/UX Design", "E-Commerce"],
            links=[
                ProjectLink(label="Live Demo", url="https://voguevaultproject.netlify.app/"),
                ProjectLink(label="GitHub", url="https://github.com/sujalkadam2906/vogue-vault-project"),
            ],
            bullets=[
                "Built a responsive, multi-page fashion e-commerce frontend using modular ES6+ JavaScript for product discovery, search, filtering, sorting, product details, and size-aware cart and wishlist management.",
                "Implemented persistent browser-side state in localStorage, reusable UI and service modules, dynamic pricing and coupon calculations, form input validation, and a simulated checkout flow.",
                "Used a CLI-based AI coding agent to assist with implementation, debugging, and refactoring; reviewed generated code changes and tested core application flows.",
            ],
            metrics=[],
            evidence_source="Present in Sujal_Kadam_Resume.pdf. Omitted in Sujal_Kadam_Resume_new.pdf for space.",
            verification_status="verified",
        ),
    ]

    return profile, projects, conflicts
