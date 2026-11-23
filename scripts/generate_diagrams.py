"""Generates professional SVG diagram assets for AI Resume Builder documentation."""

from pathlib import Path

ASSETS_DIR = Path("docs/assets")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def generate_system_architecture() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 640" width="100%" height="100%" style="background:#FFFFFF; font-family:'Segoe UI', Helvetica, Arial, sans-serif;">
  <defs>
    <linearGradient id="tealGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#174A45" />
      <stop offset="100%" stop-color="#0F332F" />
    </linearGradient>
    <linearGradient id="copperGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#C47A42" />
      <stop offset="100%" stop-color="#A65E28" />
    </linearGradient>
    <filter id="cardShadow" x="-5%" y="-5%" width="110%" height="115%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000000" flood-opacity="0.08" />
    </filter>
    <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 8 5 L 0 9 z" fill="#174A45" />
    </marker>
  </defs>

  <!-- Title Banner -->
  <rect x="30" y="20" width="860" height="55" rx="8" fill="url(#tealGrad)" filter="url(#cardShadow)" />
  <text x="460" y="46" fill="#FFFFFF" font-size="18" font-weight="bold" text-anchor="middle" letter-spacing="0.5">AI RESUME BUILDER — HIGH-LEVEL SYSTEM ARCHITECTURE</text>
  <text x="460" y="64" fill="#E9F0ED" font-size="12" text-anchor="middle">Multi-Profile Isolation · Multi-Provider AI Cascade · Deterministic 1-Page Rendering · Local ATS Analysis</text>

  <!-- Outer Border -->
  <rect x="30" y="90" width="860" height="525" rx="8" fill="none" stroke="#D4DFD9" stroke-width="1.5" />

  <!-- Layer 1: Interface Layer -->
  <rect x="50" y="110" width="245" height="145" rx="6" fill="#F8FAF9" stroke="#174A45" stroke-width="1.5" filter="url(#cardShadow)" />
  <rect x="50" y="110" width="245" height="28" rx="6" fill="#174A45" />
  <text x="172" y="129" fill="#FFFFFF" font-size="12" font-weight="bold" text-anchor="middle">1. INTERFACE LAYER</text>
  <text x="65" y="158" fill="#263238" font-size="11" font-weight="bold">• PowerShell Wrappers:</text>
  <text x="80" y="174" fill="#475B55" font-size="10.5">resume.ps1 / setup.ps1</text>
  <text x="65" y="195" fill="#263238" font-size="11" font-weight="bold">• Python CLI (Argparse + Rich):</text>
  <text x="80" y="211" fill="#475B55" font-size="10.5">--profile, --jd, --offline, --provider</text>
  <text x="80" y="227" fill="#475B55" font-size="10.5">--list-profiles, --check-providers</text>

  <!-- Arrow 1 -> 2 -->
  <path d="M 295 182 L 340 182" stroke="#174A45" stroke-width="2" marker-end="url(#arrow)" />

  <!-- Layer 2: Profile & Security Layer -->
  <rect x="345" y="110" width="250" height="145" rx="6" fill="#F8FAF9" stroke="#174A45" stroke-width="1.5" filter="url(#cardShadow)" />
  <rect x="345" y="110" width="250" height="28" rx="6" fill="#174A45" />
  <text x="470" y="129" fill="#FFFFFF" font-size="12" font-weight="bold" text-anchor="middle">2. PROFILE &amp; DATA ISOLATION</text>
  <text x="360" y="158" fill="#263238" font-size="11" font-weight="bold">• ProfileManager (Traversal Defense):</text>
  <text x="375" y="174" fill="#475B55" font-size="10.5">Regex validation / strict directory boundary</text>
  <text x="360" y="195" fill="#263238" font-size="11" font-weight="bold">• Candidate Profiles (profiles/{id}):</text>
  <text x="375" y="211" fill="#475B55" font-size="10.5">master_profile.json / projects.json</text>
  <text x="375" y="227" fill="#475B55" font-size="10.5">profile_config.yaml (Candidate Rules)</text>

  <!-- Arrow 2 -> 3 -->
  <path d="M 595 182 L 640 182" stroke="#174A45" stroke-width="2" marker-end="url(#arrow)" />

  <!-- Layer 3: JD Analysis & Ranking Engine -->
  <rect x="645" y="110" width="225" height="145" rx="6" fill="#F8FAF9" stroke="#174A45" stroke-width="1.5" filter="url(#cardShadow)" />
  <rect x="645" y="110" width="225" height="28" rx="6" fill="#174A45" />
  <text x="757" y="129" fill="#FFFFFF" font-size="12" font-weight="bold" text-anchor="middle">3. JD ANALYSIS &amp; RANKING</text>
  <text x="660" y="158" fill="#263238" font-size="11" font-weight="bold">• JDAnalyzer &amp; Keywords:</text>
  <text x="675" y="174" fill="#475B55" font-size="10.5">Skill extraction &amp; canonical synonyms</text>
  <text x="660" y="195" fill="#263238" font-size="11" font-weight="bold">• ProjectSelector (Weighted):</text>
  <text x="675" y="211" fill="#475B55" font-size="10.5">Skills (45%), Responsibilities (25%)</text>
  <text x="675" y="227" fill="#475B55" font-size="10.5">Profile Fixed Rules (e.g., Slot #2 Lock)</text>

  <!-- Arrow 3 -> 4 (Downwards) -->
  <path d="M 757 255 L 757 285 L 460 285 L 460 310" stroke="#174A45" stroke-width="2" marker-end="url(#arrow)" />

  <!-- Layer 4: AI Provider Cascade & Privacy Layer -->
  <rect x="50" y="315" width="820" height="130" rx="6" fill="#F8FAF9" stroke="#C47A42" stroke-width="1.5" filter="url(#cardShadow)" />
  <rect x="50" y="315" width="820" height="28" rx="6" fill="#C47A42" />
  <text x="460" y="334" fill="#FFFFFF" font-size="12" font-weight="bold" text-anchor="middle">4. MULTI-PROVIDER AI CASCADE &amp; PRIVACY SANITIZER</text>

  <rect x="65" y="355" width="130" height="72" rx="4" fill="#FFFFFF" stroke="#174A45" stroke-width="1.2" />
  <text x="130" y="375" fill="#174A45" font-size="11" font-weight="bold" text-anchor="middle">Google Gemini</text>
  <text x="130" y="392" fill="#475B55" font-size="9.5" text-anchor="middle">Gen AI SDK 2.0</text>
  <text x="130" y="408" fill="#0F5132" font-size="9" font-weight="bold" text-anchor="middle">Primary Provider</text>

  <text x="205" y="395" fill="#C47A42" font-size="14" font-weight="bold">→</text>

  <rect x="220" y="355" width="115" height="72" rx="4" fill="#FFFFFF" stroke="#D4DFD9" stroke-width="1" />
  <text x="277" y="375" fill="#263238" font-size="11" font-weight="bold" text-anchor="middle">Groq API</text>
  <text x="277" y="392" fill="#475B55" font-size="9.5" text-anchor="middle">Llama 3.3 70B</text>
  <text x="277" y="408" fill="#666666" font-size="9" text-anchor="middle">Fallback 1</text>

  <text x="345" y="395" fill="#C47A42" font-size="14" font-weight="bold">→</text>

  <rect x="360" y="355" width="115" height="72" rx="4" fill="#FFFFFF" stroke="#D4DFD9" stroke-width="1" />
  <text x="417" y="375" fill="#263238" font-size="11" font-weight="bold" text-anchor="middle">Cohere API</text>
  <text x="417" y="392" fill="#475B55" font-size="9.5" text-anchor="middle">Command-R+</text>
  <text x="417" y="408" fill="#666666" font-size="9" text-anchor="middle">Fallback 2</text>

  <text x="485" y="395" fill="#C47A42" font-size="14" font-weight="bold">→</text>

  <rect x="500" y="355" width="115" height="72" rx="4" fill="#FFFFFF" stroke="#D4DFD9" stroke-width="1" />
  <text x="557" y="375" fill="#263238" font-size="11" font-weight="bold" text-anchor="middle">OpenRouter</text>
  <text x="557" y="392" fill="#475B55" font-size="9.5" text-anchor="middle">HTTPX Client</text>
  <text x="557" y="408" fill="#666666" font-size="9" text-anchor="middle">Fallback 3</text>

  <text x="625" y="395" fill="#C47A42" font-size="14" font-weight="bold">→</text>

  <rect x="640" y="355" width="110" height="72" rx="4" fill="#FFFFFF" stroke="#D4DFD9" stroke-width="1" />
  <text x="695" y="375" fill="#263238" font-size="11" font-weight="bold" text-anchor="middle">Cloudflare AI</text>
  <text x="695" y="392" fill="#475B55" font-size="9.5" text-anchor="middle">Workers AI</text>
  <text x="695" y="408" fill="#666666" font-size="9" text-anchor="middle">Fallback 4</text>

  <text x="760" y="395" fill="#C47A42" font-size="14" font-weight="bold">→</text>

  <rect x="775" y="355" width="85" height="72" rx="4" fill="#E9F0ED" stroke="#174A45" stroke-width="1.2" />
  <text x="817" y="375" fill="#174A45" font-size="10" font-weight="bold" text-anchor="middle">Offline Engine</text>
  <text x="817" y="392" fill="#475B55" font-size="9" text-anchor="middle">Deterministic</text>
  <text x="817" y="408" fill="#174A45" font-size="8.5" font-weight="bold" text-anchor="middle">Zero-Network</text>

  <!-- Arrow 4 -> 5 -->
  <path d="M 460 445 L 460 470" stroke="#174A45" stroke-width="2" marker-end="url(#arrow)" />

  <!-- Layer 5: Output Generation & ATS Validation Layer -->
  <rect x="50" y="475" width="395" height="120" rx="6" fill="#F8FAF9" stroke="#174A45" stroke-width="1.5" filter="url(#cardShadow)" />
  <rect x="50" y="475" width="395" height="26" rx="6" fill="#174A45" />
  <text x="247" y="493" fill="#FFFFFF" font-size="11.5" font-weight="bold" text-anchor="middle">5. DOCUMENT RENDERING ENGINE</text>
  <text x="65" y="520" fill="#263238" font-size="11" font-weight="bold">• ReportLab PDF Renderer:</text>
  <text x="80" y="536" fill="#475B55" font-size="10.5">Editorial Teal (#174A45) + Copper (#C47A42) · 1-Page Guarantee</text>
  <text x="65" y="558" fill="#263238" font-size="11" font-weight="bold">• python-docx Renderer:</text>
  <text x="80" y="574" fill="#475B55" font-size="10.5">Matching WordprocessingML borders, shading, and #267BF1 links</text>

  <rect x="475" y="475" width="395" height="120" rx="6" fill="#F8FAF9" stroke="#174A45" stroke-width="1.5" filter="url(#cardShadow)" />
  <rect x="475" y="475" width="395" height="26" rx="6" fill="#174A45" />
  <text x="672" y="493" fill="#FFFFFF" font-size="11.5" font-weight="bold" text-anchor="middle">6. ATS VALIDATION &amp; APPLICATION PACKAGE</text>
  <text x="490" y="520" fill="#263238" font-size="11" font-weight="bold">• Three-Pillar Deterministic Scorer (100 pts):</text>
  <text x="505" y="536" fill="#475B55" font-size="10.5">Format (30 pts) · JD Relevance (50 pts) · Content Quality (20 pts)</text>
  <text x="490" y="558" fill="#263238" font-size="11" font-weight="bold">• Application Output Package:</text>
  <text x="505" y="574" fill="#475B55" font-size="10.5">output/{profile_id}/{year}/{app}/ (PDF, DOCX, PNG, ATS_Report)</text>

</svg>"""


def generate_multi_profile_isolation() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 500" width="100%" height="100%" style="background:#FFFFFF; font-family:'Segoe UI', Helvetica, Arial, sans-serif;">
  <defs>
    <linearGradient id="tealGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#174A45" />
      <stop offset="100%" stop-color="#0F332F" />
    </linearGradient>
    <linearGradient id="shieldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#C47A42" />
      <stop offset="100%" stop-color="#A65E28" />
    </linearGradient>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%">
      <feDropShadow dx="0" dy="3" stdDeviation="5" flood-color="#000000" flood-opacity="0.08" />
    </filter>
  </defs>

  <!-- Title -->
  <rect x="30" y="20" width="820" height="50" rx="8" fill="url(#tealGrad)" filter="url(#shadow)" />
  <text x="440" y="44" fill="#FFFFFF" font-size="16" font-weight="bold" text-anchor="middle">MULTI-PROFILE SECURITY &amp; ZERO-LEAKAGE BOUNDARY</text>
  <text x="440" y="60" fill="#E9F0ED" font-size="11" text-anchor="middle">Filesystem Directory Partitioning · SHA-256 Migration Integrity · Path Traversal Defense</text>

  <!-- Central Security Shield / Boundary -->
  <line x1="440" y1="95" x2="440" y2="475" stroke="#C47A42" stroke-width="2.5" stroke-dasharray="6,4" />
  <rect x="380" y="260" width="120" height="34" rx="17" fill="url(#shieldGrad)" filter="url(#shadow)" />
  <text x="440" y="282" fill="#FFFFFF" font-size="11" font-weight="bold" text-anchor="middle">STRICT ISOLATION</text>

  <!-- Left Side: Candidate Profile A (Private / Sujal) -->
  <rect x="40" y="100" width="370" height="365" rx="8" fill="#F8FAF9" stroke="#174A45" stroke-width="1.5" filter="url(#shadow)" />
  <rect x="40" y="100" width="370" height="32" rx="8" fill="#174A45" />
  <text x="225" y="122" fill="#FFFFFF" font-size="12" font-weight="bold" text-anchor="middle">PROFILE: sujal (Private Verified Candidate)</text>

  <rect x="60" y="145" width="330" height="60" rx="5" fill="#FFFFFF" stroke="#D4DFD9" />
  <text x="75" y="167" fill="#174A45" font-size="11" font-weight="bold">Candidate Directory: profiles/sujal/</text>
  <text x="75" y="185" fill="#475B55" font-size="10">• master_profile.json (Verified candidate records)</text>
  <text x="75" y="198" fill="#475B55" font-size="10">• projects.json (6 verified projects including Bearing Fault)</text>

  <rect x="60" y="215" width="330" height="60" rx="5" fill="#FFFFFF" stroke="#D4DFD9" />
  <text x="75" y="237" fill="#174A45" font-size="11" font-weight="bold">Candidate Rules: profile_config.yaml</text>
  <text x="75" y="255" fill="#475B55" font-size="10">• Fixed Project: Bearing Fault locked at Position #2</text>
  <text x="75" y="268" fill="#475B55" font-size="10">• Prohibited Terms: ["mechanical engineering"]</text>

  <rect x="60" y="285" width="330" height="60" rx="5" fill="#FFFFFF" stroke="#D4DFD9" />
  <text x="75" y="307" fill="#174A45" font-size="11" font-weight="bold">Source Resumes &amp; Audit Logs</text>
  <text x="75" y="325" fill="#475B55" font-size="10">• profiles/sujal/source_resumes/ (Original PDFs)</text>
  <text x="75" y="338" fill="#475B55" font-size="10">• profiles/sujal/audit/migration_audit.json (SHA-256)</text>

  <rect x="60" y="355" width="330" height="50" rx="5" fill="#E9F0ED" stroke="#174A45" />
  <text x="75" y="375" fill="#174A45" font-size="11" font-weight="bold">Segregated Output Directory</text>
  <text x="75" y="393" fill="#174A45" font-size="10">output/sujal/{year}/{Company}_{Role}_{Date}/</text>

  <text x="75" y="440" fill="#0F5132" font-size="10.5" font-weight="bold">✓ 0% Leaked into Demo Candidate or GitHub Repository</text>

  <!-- Right Side: Candidate Profile B (Synthetic Demo Candidate) -->
  <rect x="470" y="100" width="370" height="365" rx="8" fill="#F8FAF9" stroke="#C47A42" stroke-width="1.5" filter="url(#shadow)" />
  <rect x="470" y="100" width="370" height="32" rx="8" fill="#C47A42" />
  <text x="655" y="122" fill="#FFFFFF" font-size="12" font-weight="bold" text-anchor="middle">PROFILE: demo_candidate (Synthetic Public Fixture)</text>

  <rect x="490" y="145" width="330" height="60" rx="5" fill="#FFFFFF" stroke="#D4DFD9" />
  <text x="505" y="167" fill="#A65E28" font-size="11" font-weight="bold">Candidate Directory: profiles/demo_candidate/</text>
  <text x="505" y="185" fill="#475B55" font-size="10">• Aarav Sharma (Fictional Frontend Developer)</text>
  <text x="505" y="198" fill="#475B55" font-size="10">• 4 verified frontend projects (CloudCanvas, CryptoPulse)</text>

  <rect x="490" y="215" width="330" height="60" rx="5" fill="#FFFFFF" stroke="#D4DFD9" />
  <text x="505" y="237" fill="#A65E28" font-size="11" font-weight="bold">Candidate Rules: profile_config.yaml</text>
  <text x="505" y="255" fill="#475B55" font-size="10">• Pure Dynamic Ranking (has_fixed_project: false)</text>
  <text x="505" y="268" fill="#475B55" font-size="10">• Prohibited Terms: [] (Degree: Computer Science)</text>

  <rect x="490" y="285" width="330" height="60" rx="5" fill="#FFFFFF" stroke="#D4DFD9" />
  <text x="505" y="307" fill="#A65E28" font-size="11" font-weight="bold">Synthetic Mark &amp; Safety Flag</text>
  <text x="505" y="325" fill="#475B55" font-size="10">• is_synthetic: true (Explicit fixture marker)</text>
  <text x="505" y="338" fill="#475B55" font-size="10">• Safe for public GitHub portfolio publication</text>

  <rect x="490" y="355" width="330" height="50" rx="5" fill="#FDF3EB" stroke="#C47A42" />
  <text x="505" y="375" fill="#A65E28" font-size="11" font-weight="bold">Segregated Output Directory</text>
  <text x="505" y="393" fill="#A65E28" font-size="10">output/demo_candidate/{year}/{Company}_{Role}_{Date}/</text>

  <text x="505" y="440" fill="#A65E28" font-size="10.5" font-weight="bold">✓ 0% Private Candidate Data Contained in Fixture</text>

</svg>"""


def generate_ats_scoring_breakdown() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 840 440" width="100%" height="100%" style="background:#FFFFFF; font-family:'Segoe UI', Helvetica, Arial, sans-serif;">
  <defs>
    <linearGradient id="tealGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#174A45" />
      <stop offset="100%" stop-color="#0F332F" />
    </linearGradient>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%">
      <feDropShadow dx="0" dy="3" stdDeviation="5" flood-color="#000000" flood-opacity="0.08" />
    </filter>
  </defs>

  <rect x="30" y="20" width="780" height="50" rx="8" fill="url(#tealGrad)" filter="url(#shadow)" />
  <text x="420" y="44" fill="#FFFFFF" font-size="16" font-weight="bold" text-anchor="middle">THREE-PILLAR ATS READINESS SCORING METHODOLOGY</text>
  <text x="420" y="60" fill="#E9F0ED" font-size="11" text-anchor="middle">Deterministic Heuristic Assessment Based on Actual Extracted PDF Text (Total: 100 Points)</text>

  <!-- Pillar 1: Format Compatibility (30 pts) -->
  <rect x="40" y="95" width="235" height="310" rx="8" fill="#F8FAF9" stroke="#174A45" stroke-width="1.5" filter="url(#shadow)" />
  <rect x="40" y="95" width="235" height="34" rx="8" fill="#174A45" />
  <text x="157" y="117" fill="#FFFFFF" font-size="12" font-weight="bold" text-anchor="middle">FORMAT COMPATIBILITY</text>
  <text x="157" y="148" fill="#174A45" font-size="22" font-weight="bold" text-anchor="middle">30 Points</text>
  <text x="157" y="165" fill="#475B55" font-size="10.5" text-anchor="middle">Weight: 30%</text>

  <line x1="55" y1="180" x2="260" y2="180" stroke="#D4DFD9" stroke-width="1" />
  <text x="55" y="202" fill="#263238" font-size="10.5" font-weight="bold">• Single Column Layout: +5</text>
  <text x="55" y="222" fill="#263238" font-size="10.5" font-weight="bold">• Exactly 1 Page Fit: +8</text>
  <text x="55" y="242" fill="#263238" font-size="10.5" font-weight="bold">• Contact Info Complete: +5</text>
  <text x="55" y="262" fill="#263238" font-size="10.5" font-weight="bold">• Standard Headings: +4</text>
  <text x="55" y="282" fill="#263238" font-size="10.5" font-weight="bold">• Selectable PDF Text: +4</text>
  <text x="55" y="302" fill="#263238" font-size="10.5" font-weight="bold">• Zero Prohibited Terms: +4</text>

  <rect x="55" y="335" width="205" height="50" rx="4" fill="#E9F0ED" />
  <text x="157" y="355" fill="#174A45" font-size="9.5" font-weight="bold" text-anchor="middle">Validation Engine</text>
  <text x="157" y="372" fill="#475B55" font-size="9" text-anchor="middle">pypdf &amp; pdfplumber extraction</text>

  <!-- Pillar 2: JD Relevance (50 pts) -->
  <rect x="300" y="95" width="240" height="310" rx="8" fill="#F8FAF9" stroke="#C47A42" stroke-width="1.5" filter="url(#shadow)" />
  <rect x="300" y="95" width="240" height="34" rx="8" fill="#C47A42" />
  <text x="420" y="117" fill="#FFFFFF" font-size="12" font-weight="bold" text-anchor="middle">JD RELEVANCE</text>
  <text x="420" y="148" fill="#C47A42" font-size="22" font-weight="bold" text-anchor="middle">50 Points</text>
  <text x="420" y="165" fill="#475B55" font-size="10.5" text-anchor="middle">Weight: 50%</text>

  <line x1="315" y1="180" x2="525" y2="180" stroke="#D4DFD9" stroke-width="1" />
  <text x="315" y="202" fill="#263238" font-size="10.5" font-weight="bold">• Must-Have Skills Match: 35 pts</text>
  <text x="330" y="218" fill="#475B55" font-size="9.5">Linear scaling by verified coverage</text>
  <text x="315" y="238" fill="#263238" font-size="10.5" font-weight="bold">• Preferred Skills Match: 10 pts</text>
  <text x="330" y="254" fill="#475B55" font-size="9.5">Bonus coverage for secondary skills</text>
  <text x="315" y="274" fill="#263238" font-size="10.5" font-weight="bold">• Keyword Density Ratio: 5 pts</text>
  <text x="330" y="290" fill="#475B55" font-size="9.5">Natural contextual frequency</text>
  <text x="315" y="310" fill="#C47A42" font-size="10" font-weight="bold">• Unsupported Claims: Truthfully Left</text>

  <rect x="315" y="335" width="210" height="50" rx="4" fill="#FDF3EB" />
  <text x="420" y="355" fill="#C47A42" font-size="9.5" font-weight="bold" text-anchor="middle">Synonym Matching</text>
  <text x="420" y="372" fill="#475B55" font-size="9" text-anchor="middle">Canonical technical taxonomy</text>

  <!-- Pillar 3: Content Quality (20 pts) -->
  <rect x="565" y="95" width="235" height="310" rx="8" fill="#F8FAF9" stroke="#174A45" stroke-width="1.5" filter="url(#shadow)" />
  <rect x="565" y="95" width="235" height="34" rx="8" fill="#174A45" />
  <text x="682" y="117" fill="#FFFFFF" font-size="12" font-weight="bold" text-anchor="middle">CONTENT QUALITY</text>
  <text x="682" y="148" fill="#174A45" font-size="22" font-weight="bold" text-anchor="middle">20 Points</text>
  <text x="682" y="165" fill="#475B55" font-size="10.5" text-anchor="middle">Weight: 20%</text>

  <line x1="580" y1="180" x2="785" y2="180" stroke="#D4DFD9" stroke-width="1" />
  <text x="580" y="202" fill="#263238" font-size="10.5" font-weight="bold">• Strong Action Verbs: +8</text>
  <text x="595" y="218" fill="#475B55" font-size="9.5">Engineered, Architected, Built, etc.</text>
  <text x="580" y="238" fill="#263238" font-size="10.5" font-weight="bold">• Quantifiable Metrics: +6</text>
  <text x="595" y="254" fill="#475B55" font-size="9.5">Percentages, latencies, user volumes</text>
  <text x="580" y="274" fill="#263238" font-size="10.5" font-weight="bold">• Bullet Conciseness: +3</text>
  <text x="595" y="290" fill="#475B55" font-size="9.5">1-2 lines max per bullet point</text>
  <text x="580" y="310" fill="#263238" font-size="10.5" font-weight="bold">• Evidence Verification: +3</text>

  <rect x="580" y="335" width="205" height="50" rx="4" fill="#E9F0ED" />
  <text x="682" y="355" fill="#174A45" font-size="9.5" font-weight="bold" text-anchor="middle">Anti-Hallucination</text>
  <text x="682" y="372" fill="#475B55" font-size="9" text-anchor="middle">Strict candidate database bounds</text>

</svg>"""


def main():
    (ASSETS_DIR / "system_architecture.svg").write_text(generate_system_architecture(), encoding="utf-8")
    (ASSETS_DIR / "multi_profile_isolation.svg").write_text(generate_multi_profile_isolation(), encoding="utf-8")
    (ASSETS_DIR / "ats_scoring_breakdown.svg").write_text(generate_ats_scoring_breakdown(), encoding="utf-8")
    print("Successfully generated all SVG diagrams in docs/assets/!")


if __name__ == "__main__":
    main()
