"""Unified Design System defining Times New Roman typography, Editorial Teal & Copper palette, page geometry, and border."""

from reportlab.lib import colors

# ==============================================================================
# 1. COLOR PALETTE (Editorial Deep Teal & Warm Copper Palette)
# ==============================================================================
HEX_PRIMARY_TEAL = "#174A45"        # Primary Deep Teal: Candidate name, section headings, outer border, hyperlinks
HEX_WARM_COPPER = "#C47A42"         # Warm Copper Accent: Section accent bars, horizontal divider rules
HEX_MAIN_GRAPHITE = "#263238"       # Main Graphite Text: High-contrast body text, bullet points
HEX_SECONDARY_TEXT = "#475B55"      # Secondary Text: Dates, locations, contact info, tech stacks, metadata
HEX_PALE_MINT = "#E9F0ED"           # Pale Mint Section Background: subtle heading band shading
HEX_LIGHT_DIVIDER = "#D4DFD9"       # Light Divider: Subtle header rules, hairline separators
HEX_BACKGROUND = "#FFFFFF"          # Pure white page background
HEX_HYPERLINK = "#267BF1"           # Hyperlink Blue: All clickable external links, DOIs, repositories

# Backward-compatible aliases for existing component references and previous themes
HEX_FOREST_GREEN = HEX_PRIMARY_TEAL
HEX_SECONDARY_SAGE = HEX_WARM_COPPER
HEX_LIGHT_SAGE_GREY = HEX_LIGHT_DIVIDER
HEX_BODY_CHARCOAL = HEX_MAIN_GRAPHITE
HEX_PRIMARY_FOREST = HEX_PRIMARY_TEAL
HEX_DEEP_SLATE_NAVY = HEX_PRIMARY_TEAL
HEX_MUTED_BLUE = HEX_WARM_COPPER
HEX_SOFT_BLUE_GREY = HEX_LIGHT_DIVIDER
HEX_BODY_TEXT = HEX_MAIN_GRAPHITE
HEX_PRIMARY_NAVY = HEX_PRIMARY_TEAL
HEX_SECONDARY_TEAL = HEX_WARM_COPPER
HEX_MAIN_TEXT = HEX_MAIN_GRAPHITE
HEX_SEPARATOR = HEX_LIGHT_DIVIDER

# ReportLab Color Objects
COLOR_PRIMARY_TEAL = colors.HexColor(HEX_PRIMARY_TEAL)
COLOR_WARM_COPPER = colors.HexColor(HEX_WARM_COPPER)
COLOR_MAIN_GRAPHITE = colors.HexColor(HEX_MAIN_GRAPHITE)
COLOR_SECONDARY_TEXT = colors.HexColor(HEX_SECONDARY_TEXT)
COLOR_PALE_MINT = colors.HexColor(HEX_PALE_MINT)
COLOR_LIGHT_DIVIDER = colors.HexColor(HEX_LIGHT_DIVIDER)
COLOR_BACKGROUND = colors.HexColor(HEX_BACKGROUND)
COLOR_HYPERLINK = colors.HexColor(HEX_HYPERLINK)

# Page Border & Section Divider
COLOR_PAGE_BORDER = colors.HexColor(HEX_PRIMARY_TEAL)
PAGE_BORDER_WIDTH_PT = 1.5          # 1.5 pt prominent outer border in Deep Teal

HEX_SECTION_DIVIDER = HEX_WARM_COPPER
COLOR_SECTION_DIVIDER = colors.HexColor(HEX_SECTION_DIVIDER)
SECTION_DIVIDER_WIDTH_PT = 1.3      # 1.3 pt warm copper horizontal line directly below headings

# Project Tech Stack Styling (Readable Deep Sage/Slate #475B55)
HEX_PROJECT_TECH = "#475B55"
COLOR_PROJECT_TECH = colors.HexColor(HEX_PROJECT_TECH)

# Component Color Aliases
COLOR_FOREST_GREEN = COLOR_PRIMARY_TEAL
COLOR_SECONDARY_SAGE = COLOR_WARM_COPPER
COLOR_LIGHT_SAGE_GREY = COLOR_LIGHT_DIVIDER
COLOR_BODY_CHARCOAL = COLOR_MAIN_GRAPHITE
COLOR_PRIMARY_NAVY = COLOR_PRIMARY_TEAL
COLOR_MUTED_BLUE = COLOR_WARM_COPPER
COLOR_SOFT_BLUE_GREY = COLOR_LIGHT_DIVIDER
COLOR_SEPARATOR = COLOR_LIGHT_DIVIDER
COLOR_MAIN_TEXT = COLOR_MAIN_GRAPHITE

# ==============================================================================
# 2. PAGE GEOMETRY (A4 Portrait, consistent margins)
# ==============================================================================
PAGE_WIDTH_PT = 595.27              # Standard A4 width in points (8.27 in)
PAGE_HEIGHT_PT = 841.89             # Standard A4 height in points (11.69 in)

# Margins: Left/Right ~0.55 in (39.6 pt), Top/Bottom ~0.44 in (32.0 pt)
MARGIN_LEFT_PT = 39.6               # 0.55 inch
MARGIN_RIGHT_PT = 39.6              # 0.55 inch
MARGIN_TOP_PT = 32.0                # ~0.44 inch
MARGIN_BOTTOM_PT = 32.0             # ~0.44 inch

# Outer decorative border: 0.30 inch (21.6 pt) from page edges
PAGE_BORDER_INSET_PT = 21.6

USABLE_WIDTH_PT = PAGE_WIDTH_PT - (MARGIN_LEFT_PT + MARGIN_RIGHT_PT)    # 516.07 pt
USABLE_HEIGHT_PT = PAGE_HEIGHT_PT - (MARGIN_TOP_PT + MARGIN_BOTTOM_PT)  # 777.89 pt

# Target vertical area utilization: 84% to 92% of USABLE_HEIGHT_PT
MIN_VERTICAL_UTILIZATION_PT = USABLE_HEIGHT_PT * 0.84  # ~653.4 pt
MAX_VERTICAL_UTILIZATION_PT = USABLE_HEIGHT_PT * 0.94  # ~731.2 pt

# ==============================================================================
# 3. TYPOGRAPHY SCALES (Times New Roman / Serif)
# ==============================================================================
FONT_SERIF_REGULAR = "Times-Roman"
FONT_SERIF_BOLD = "Times-Bold"
FONT_SERIF_ITALIC = "Times-Italic"
FONT_SERIF_BOLD_ITALIC = "Times-BoldItalic"

FONT_CANDIDATE_NAME = 20.0
LEADING_CANDIDATE_NAME = 22.5

FONT_TARGET_TITLE = 10.5            # Permanent headline
LEADING_TARGET_TITLE = 12.5

FONT_TECH_SUBTITLE = 9.0
LEADING_TECH_SUBTITLE = 11.0

FONT_CONTACT = 8.8
LEADING_CONTACT = 11.0

FONT_SECTION_HEADING = 10.5
LEADING_SECTION_HEADING = 12.0

FONT_PROJECT_TITLE = 10.0
LEADING_PROJECT_TITLE = 11.8

FONT_PROJECT_TECH = 9.2
LEADING_PROJECT_TECH = 11.0

FONT_BODY = 9.6                     # Strict rule: never below 9.5 pt!
LEADING_BODY = 11.2

FONT_BULLET = 9.6                   # Strict rule: never below 9.5 pt!
LEADING_BULLET = 11.2
