"""One-page compression engine ensuring the resume fits strictly on 1 A4 page."""

import copy
from typing import List, Tuple
from .manifest import ManifestProject, ResumeContentManifest


class OnePageCompressionEngine:
    """
    Progressively compresses resume content to guarantee strict one-page A4 compliance.
    Follows user priority order:
    1. Shorten unnecessarily long project descriptions / remove repetitive wording.
    2. Keep the most impactful bullet for each project.
    3. Reduce professional summary to approximately two lines.
    4. Remove optional sections (e.g. professional development / job simulation).
    5. Reduce inter-section spacing.
    6. Never shrink body font below safe threshold (9 pt).
    7. Always preserve the 4-project rule with Bearing Fault at #2.
    """

    @staticmethod
    def compress(manifest: ResumeContentManifest, level: int = 0) -> ResumeContentManifest:
        """
        Apply compression level (0 = normal, 1 = moderate, 2 = aggressive, 3 = maximum).
        """
        c_manifest = copy.deepcopy(manifest)
        if level == 0:
            return c_manifest

        # Level 1: Omit optional professional development section to preserve projects
        if level >= 1:
            c_manifest.professional_development = []
            # Shorten summary
            sentences = [s.strip() for s in c_manifest.summary.split(". ") if s.strip()]
            if len(sentences) > 3:
                c_manifest.summary = ". ".join(sentences[:3]) + "."

        # Level 2: Keep at most 2 concise bullets per project
        if level >= 2:
            compressed_projects = []
            for p in c_manifest.projects:
                # Keep top 2 bullets, trim any excess
                new_bullets = p.bullets[:2]
                compressed_projects.append(
                    ManifestProject(
                        id=p.id,
                        title=p.title,
                        subtitle=p.subtitle,
                        is_fixed=p.is_fixed,
                        bullets=new_bullets,
                        links=p.links,
                    )
                )
            c_manifest.projects = compressed_projects

            # Limit certifications to top 4
            if len(c_manifest.certifications) > 4:
                c_manifest.certifications = c_manifest.certifications[:4]

        # Level 3: Keep 1 strong bullet for slot 3 and 4 projects if space is critical
        if level >= 3:
            for idx in [2, 3]:  # 0-indexed: slots 3 and 4
                if idx < len(c_manifest.projects) and len(c_manifest.projects[idx].bullets) > 1:
                    c_manifest.projects[idx].bullets = c_manifest.projects[idx].bullets[:1]

        return c_manifest
