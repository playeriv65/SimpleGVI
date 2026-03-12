"""
Apple Design Tokens for SimpleGVI Streamlit App.

Comprehensive Apple design system variables for a clean, professional,
and Apple-like interface with generous whitespace and refined details.
"""

APPLE_DESIGN_TOKENS = """
/* ============================================
   APPLE DESIGN TOKENS - SimpleGVI Streamlit App
   ============================================ */

/* --------------------------------------------
   COLOR PALETTE
   -------------------------------------------- */
:root {
  /* Background Colors */
  --apple-bg-primary: #F5F5F7;
  --apple-bg-card: #FFFFFF;
  
  /* Text Colors */
  --apple-text-primary: #1D1D1F;
  --apple-text-secondary: #86868B;
  --apple-text-tertiary: #6E6E73;
  
  /* Accent Colors */
  --apple-success: #34C759;
  --apple-primary: #34C759;
  --apple-accent-blue: #007AFF;
  --apple-warning: #FF9500;
  --apple-error: #FF3B30;
  
  /* UI Colors */
  --apple-separator: rgba(0, 0, 0, 0.1);
  --apple-border: rgba(0, 0, 0, 0.08);
  --apple-overlay: rgba(0, 0, 0, 0.4);
  
  /* --------------------------------------------
     TYPOGRAPHY SCALE
     -------------------------------------------- */
  --apple-font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', sans-serif;
  
  /* Font Sizes */
  --apple-text-large-title: 28px;
  --apple-text-title: 24px;
  --apple-text-headline: 20px;
  --apple-text-body: 17px;
  --apple-text-callout: 15px;
  --apple-text-footnote: 13px;
  
  /* Font Weights */
  --apple-weight-regular: 400;
  --apple-weight-medium: 500;
  --apple-weight-semibold: 600;
  --apple-weight-bold: 700;
  
  /* Line Heights */
  --apple-line-height-tight: 1.2;
  --apple-line-height-normal: 1.5;
  --apple-line-height-relaxed: 1.75;
  
  /* Letter Spacing */
  --apple-letter-spacing-tight: -0.5px;
  --apple-letter-spacing-normal: -0.3px;
  --apple-letter-spacing-none: 0;
  
  /* --------------------------------------------
     SPACING SCALE (8pt Grid)
     -------------------------------------------- */
  --apple-space-xs: 4px;
  --apple-space-sm: 8px;
  --apple-space-md: 16px;
  --apple-space-lg: 24px;
  --apple-space-xl: 32px;
  --apple-space-xxl: 40px;
  --apple-space-xxxl: 48px;
  
  /* --------------------------------------------
     SHADOWS
     -------------------------------------------- */
  --apple-shadow-card: 0 4px 24px rgba(0, 0, 0, 0.04);
  --apple-shadow-elevated: 0 8px 32px rgba(0, 0, 0, 0.08);
  --apple-shadow-button: 0 2px 8px rgba(0, 0, 0, 0.08);
  --apple-shadow-dropdown: 0 12px 40px rgba(0, 0, 0, 0.12);
  --apple-shadow-modal: 0 24px 64px rgba(0, 0, 0, 0.16);
  
  /* --------------------------------------------
     BORDER RADIUS
     -------------------------------------------- */
  --apple-radius-small: 8px;
  --apple-radius-medium: 10px;
  --apple-radius-large: 18px;
  --apple-radius-xl: 24px;
  --apple-radius-full: 9999px;
  
  /* --------------------------------------------
     TRANSITIONS
     -------------------------------------------- */
  --apple-transition-fast: 150ms ease;
  --apple-transition-normal: 250ms ease;
  --apple-transition-slow: 350ms ease;
  
  /* --------------------------------------------
     Z-INDEX SCALE
     -------------------------------------------- */
  --apple-z-base: 0;
  --apple-z-dropdown: 100;
  --apple-z-sticky: 200;
  --apple-z-fixed: 300;
  --apple-z-modal-backdrop: 400;
  --apple-z-modal: 500;
  --apple-z-popover: 600;
  --apple-z-tooltip: 700;
}

/* --------------------------------------------
   UTILITY CLASSES
   -------------------------------------------- */

/* Typography Utilities */
.apple-text-large-title {
  font-size: var(--apple-text-large-title);
  font-weight: var(--apple-weight-semibold);
  letter-spacing: var(--apple-letter-spacing-tight);
  line-height: var(--apple-line-height-tight);
  color: var(--apple-text-primary);
}

.apple-text-title {
  font-size: var(--apple-text-title);
  font-weight: var(--apple-weight-semibold);
  letter-spacing: var(--apple-letter-spacing-tight);
  line-height: var(--apple-line-height-tight);
  color: var(--apple-text-primary);
}

.apple-text-headline {
  font-size: var(--apple-text-headline);
  font-weight: var(--apple-weight-semibold);
  letter-spacing: var(--apple-letter-spacing-normal);
  line-height: var(--apple-line-height-tight);
  color: var(--apple-text-primary);
}

.apple-text-body {
  font-size: var(--apple-text-body);
  font-weight: var(--apple-weight-regular);
  line-height: var(--apple-line-height-normal);
  color: var(--apple-text-primary);
}

.apple-text-callout {
  font-size: var(--apple-text-callout);
  font-weight: var(--apple-weight-regular);
  line-height: var(--apple-line-height-normal);
  color: var(--apple-text-secondary);
}

.apple-text-footnote {
  font-size: var(--apple-text-footnote);
  font-weight: var(--apple-weight-regular);
  line-height: var(--apple-line-height-normal);
  color: var(--apple-text-tertiary);
}

/* Spacing Utilities */
.apple-space-xs { margin: var(--apple-space-xs); }
.apple-space-sm { margin: var(--apple-space-sm); }
.apple-space-md { margin: var(--apple-space-md); }
.apple-space-lg { margin: var(--apple-space-lg); }
.apple-space-xl { margin: var(--apple-space-xl); }
.apple-space-xxl { margin: var(--apple-space-xxl); }
.apple-space-xxxl { margin: var(--apple-space-xxxl); }

/* Card Styles */
.apple-card {
  background-color: var(--apple-bg-card);
  border-radius: var(--apple-radius-large);
  box-shadow: var(--apple-shadow-card);
  padding: var(--apple-space-lg);
}

.apple-card-elevated {
  background-color: var(--apple-bg-card);
  border-radius: var(--apple-radius-large);
  box-shadow: var(--apple-shadow-elevated);
  padding: var(--apple-space-xl);
}

/* Button Styles */
.apple-button {
  background-color: var(--apple-primary);
  color: var(--apple-bg-card);
  border-radius: var(--apple-radius-medium);
  padding: var(--apple-space-sm) var(--apple-space-md);
  font-size: var(--apple-text-callout);
  font-weight: var(--apple-weight-semibold);
  box-shadow: var(--apple-shadow-button);
  transition: all var(--apple-transition-fast);
}

.apple-button:hover {
  transform: translateY(-1px);
  box-shadow: var(--apple-shadow-elevated);
}

.apple-button-secondary {
  background-color: var(--apple-bg-card);
  color: var(--apple-accent-blue);
  border: 1px solid var(--apple-border);
}

.apple-button-ghost {
  background-color: transparent;
  color: var(--apple-accent-blue);
}

/* Input Styles */
.apple-input {
  background-color: var(--apple-bg-card);
  border: 1px solid var(--apple-border);
  border-radius: var(--apple-radius-medium);
  padding: var(--apple-space-sm) var(--apple-space-md);
  font-size: var(--apple-text-body);
  color: var(--apple-text-primary);
  transition: border-color var(--apple-transition-fast);
}

.apple-input:focus {
  border-color: var(--apple-accent-blue);
  outline: none;
}

/* Status Colors */
.apple-status-success { color: var(--apple-success); }
.apple-status-warning { color: var(--apple-warning); }
.apple-status-error { color: var(--apple-error); }
.apple-status-info { color: var(--apple-accent-blue); }

/* Separator */
.apple-separator {
  height: 1px;
  background-color: var(--apple-separator);
  margin: var(--apple-space-md) 0;
}

/* Container */
.apple-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--apple-space-lg);
}

/* Background Utilities */
.apple-bg-primary { background-color: var(--apple-bg-primary); }
.apple-bg-card { background-color: var(--apple-bg-card); }
"""

# Export for use in Streamlit apps
__all__ = ["APPLE_DESIGN_TOKENS"]
