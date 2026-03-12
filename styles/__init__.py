"""
Apple Design System Styles for SimpleGVI Streamlit App.

Combines design tokens, components, and animations into a unified stylesheet.
"""

from .apple_design_tokens import APPLE_DESIGN_TOKENS


def get_apple_styles() -> str:
    """Combine all Apple design CSS modules."""
    css_parts = [APPLE_DESIGN_TOKENS]

    try:
        from .apple_components import APPLE_COMPONENTS_CSS

        css_parts.append(APPLE_COMPONENTS_CSS)
    except ImportError:
        pass

    try:
        from .apple_animations import APPLE_ANIMATIONS_CSS

        css_parts.append(APPLE_ANIMATIONS_CSS)
    except ImportError:
        pass

    return "\n".join(css_parts)


__all__ = ["APPLE_DESIGN_TOKENS", "get_apple_styles"]
