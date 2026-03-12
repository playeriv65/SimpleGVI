"""
Apple CSS Components Library for SimpleGVI Streamlit App.

Streamlit-specific component styles that extend the Apple design tokens.
Targets Streamlit's DOM structure for seamless integration.
"""

from styles.apple_design_tokens import APPLE_DESIGN_TOKENS

_COMPONENT_CSS = """
/* ============================================
   APPLE COMPONENTS - Streamlit Integration
   ============================================ */

/* --------------------------------------------
   GLOBAL OVERRIDES
   -------------------------------------------- */

/* Main app background */
.stApp {
  background-color: var(--apple-bg-primary);
  font-family: var(--apple-font-family);
}

/* Remove default Streamlit padding */
.block-container {
  padding: var(--apple-space-lg) var(--apple-space-xl) var(--apple-space-xxxl) var(--apple-space-xl);
  max-width: 100%;
}

/* --------------------------------------------
   CARDS
   -------------------------------------------- */

/* Apple card wrapper class */
.apple-card {
  background-color: var(--apple-bg-card);
  border-radius: var(--apple-radius-large);
  box-shadow: var(--apple-shadow-card);
  padding: var(--apple-space-lg);
  transition: all var(--apple-transition-normal);
}

.apple-card:hover {
  box-shadow: var(--apple-shadow-elevated);
  transform: translateY(-2px);
}

/* Streamlit container as card */
.element-container:has(.apple-card) {
  margin-bottom: var(--apple-space-lg);
}

/* Card with elevated styling */
.apple-card-elevated {
  background-color: var(--apple-bg-card);
  border-radius: var(--apple-radius-large);
  box-shadow: var(--apple-shadow-elevated);
  padding: var(--apple-space-xl);
}

/* --------------------------------------------
   BUTTONS
   -------------------------------------------- */

/* Primary Button */
.stButton button {
  background-color: var(--apple-success) !important;
  color: var(--apple-bg-card) !important;
  border-radius: var(--apple-radius-medium) !important;
  padding: var(--apple-space-sm) var(--apple-space-lg) !important;
  font-size: var(--apple-text-callout) !important;
  font-weight: var(--apple-weight-semibold) !important;
  font-family: var(--apple-font-family) !important;
  border: none !important;
  box-shadow: var(--apple-shadow-button) !important;
  transition: all var(--apple-transition-fast) !important;
  cursor: pointer;
  min-height: 40px;
}

.stButton button:hover {
  background-color: #2DB34D !important;
  box-shadow: var(--apple-shadow-elevated) !important;
  transform: translateY(-1px) !important;
}

.stButton button:active {
  background-color: #28A343 !important;
  transform: translateY(0) !important;
  box-shadow: var(--apple-shadow-button) !important;
}

.stButton button:disabled,
.stButton button[disabled] {
  background-color: #E5E5EA !important;
  color: #8E8E93 !important;
  cursor: not-allowed !important;
  transform: none !important;
  box-shadow: none !important;
}

/* Secondary Button */
.stButton button[kind="secondary"] {
  background-color: transparent !important;
  color: var(--apple-accent-blue) !important;
  border: 1px solid var(--apple-border) !important;
  box-shadow: none !important;
}

.stButton button[kind="secondary"]:hover {
  background-color: rgba(0, 122, 255, 0.05) !important;
  border-color: var(--apple-accent-blue) !important;
}

.stButton button[kind="secondary"]:active {
  background-color: rgba(0, 122, 255, 0.1) !important;
}

/* Ghost Button */
.stButton button[kind="ghost"] {
  background-color: transparent !important;
  color: var(--apple-accent-blue) !important;
  border: none !important;
  box-shadow: none !important;
}

.stButton button[kind="ghost"]:hover {
  background-color: rgba(0, 122, 255, 0.05) !important;
}

/* --------------------------------------------
   INPUTS
   -------------------------------------------- */

/* Text Input */
.stTextInput input {
  background-color: var(--apple-bg-card);
  border: 1px solid var(--apple-border);
  border-radius: var(--apple-radius-medium);
  padding: var(--apple-space-sm) var(--apple-space-md);
  font-size: var(--apple-text-body);
  font-family: var(--apple-font-family);
  color: var(--apple-text-primary);
  min-height: 40px;
  transition: all var(--apple-transition-fast);
}

.stTextInput input:hover {
  border-color: rgba(0, 0, 0, 0.15);
}

.stTextInput input:focus {
  border-color: var(--apple-accent-blue);
  box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.15);
  outline: none;
}

.stTextInput input:disabled {
  background-color: #F5F5F7;
  color: var(--apple-text-secondary);
  cursor: not-allowed;
}

/* Number Input */
.stNumberInput input {
  background-color: var(--apple-bg-card);
  border: 1px solid var(--apple-border);
  border-radius: var(--apple-radius-medium);
  padding: var(--apple-space-sm) var(--apple-space-md);
  font-size: var(--apple-text-body);
  font-family: var(--apple-font-family);
  color: var(--apple-text-primary);
  min-height: 40px;
  transition: all var(--apple-transition-fast);
}

.stNumberInput input:focus {
  border-color: var(--apple-accent-blue);
  box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.15);
  outline: none;
}

/* Text Area */
.stTextArea textarea {
  background-color: var(--apple-bg-card);
  border: 1px solid var(--apple-border);
  border-radius: var(--apple-radius-medium);
  padding: var(--apple-space-sm) var(--apple-space-md);
  font-size: var(--apple-text-body);
  font-family: var(--apple-font-family);
  color: var(--apple-text-primary);
  min-height: 100px;
  transition: all var(--apple-transition-fast);
  resize: vertical;
}

.stTextArea textarea:focus {
  border-color: var(--apple-accent-blue);
  box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.15);
  outline: none;
}

/* Selectbox */
.stSelectbox select,
[data-testid="stSelectbox"] select {
  background-color: var(--apple-bg-card);
  border: 1px solid var(--apple-border);
  border-radius: var(--apple-radius-medium);
  padding: var(--apple-space-sm) var(--apple-space-md);
  font-size: var(--apple-text-body);
  font-family: var(--apple-font-family);
  color: var(--apple-text-primary);
  min-height: 40px;
  cursor: pointer;
  transition: all var(--apple-transition-fast);
}

.stSelectbox select:focus,
[data-testid="stSelectbox"] select:focus {
  border-color: var(--apple-accent-blue);
  box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.15);
  outline: none;
}

/* Multiselect */
.stMultiSelect [data-baseweb="select"] {
  background-color: var(--apple-bg-card);
  border: 1px solid var(--apple-border);
  border-radius: var(--apple-radius-medium);
  min-height: 40px;
}

.stMultiSelect [data-baseweb="select"]:focus-within {
  border-color: var(--apple-accent-blue);
  box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.15);
}

/* --------------------------------------------
   FILE UPLOADER
   -------------------------------------------- */

/* File Uploader Dropzone */
.stFileUploader {
  background-color: var(--apple-bg-card);
  border: 2px dashed var(--apple-border);
  border-radius: var(--apple-radius-large);
  padding: var(--apple-space-xl);
  transition: all var(--apple-transition-normal);
}

.stFileUploader:hover {
  border-color: var(--apple-success);
  background-color: rgba(52, 199, 89, 0.03);
}

/* Drag state */
.stFileUploader[data-drag-active="true"] {
  border-color: var(--apple-success);
  background-color: rgba(52, 199, 89, 0.05);
  transform: scale(1.01);
}

/* Upload button inside uploader */
.stFileUploader button {
  background-color: var(--apple-accent-blue) !important;
  color: white !important;
  border-radius: var(--apple-radius-medium) !important;
  padding: var(--apple-space-sm) var(--apple-space-md) !important;
  font-weight: var(--apple-weight-semibold) !important;
}

/* File info text */
.stFileUploader .uploadedFile {
  background-color: #F5F5F7;
  border-radius: var(--apple-radius-small);
  padding: var(--apple-space-sm) var(--apple-space-md);
  margin-top: var(--apple-space-sm);
}

/* --------------------------------------------
   METRICS
   -------------------------------------------- */

/* Metric container */
.stMetric {
  background-color: var(--apple-bg-card);
  border-radius: var(--apple-radius-large);
  box-shadow: var(--apple-shadow-card);
  padding: var(--apple-space-lg);
  transition: all var(--apple-transition-normal);
}

.stMetric:hover {
  box-shadow: var(--apple-shadow-elevated);
}

/* Metric value - large and prominent */
.stMetric .metric-value {
  font-size: 2.5rem;
  font-weight: var(--apple-weight-bold);
  color: var(--apple-text-primary);
  line-height: 1.2;
  letter-spacing: var(--apple-letter-spacing-tight);
}

/* Metric label */
.stMetric .metric-label {
  font-size: var(--apple-text-callout);
  font-weight: var(--apple-weight-medium);
  color: var(--apple-text-secondary);
  margin-bottom: var(--apple-space-xs);
}

/* Metric delta */
.stMetric .metric-delta {
  font-size: var(--apple-text-footnote);
  font-weight: var(--apple-weight-medium);
  margin-top: var(--apple-space-xs);
}

/* Positive delta */
.stMetric .metric-delta-positive {
  color: var(--apple-success);
}

/* Negative delta */
.stMetric .metric-delta-negative {
  color: var(--apple-error);
}

/* --------------------------------------------
   SIDEBAR
   -------------------------------------------- */

/* Sidebar container */
[data-testid="stSidebar"] {
  background-color: var(--apple-bg-card);
  border-right: 1px solid var(--apple-border);
  box-shadow: var(--apple-shadow-card);
}

[data-testid="stSidebar"] .block-container {
  padding: var(--apple-space-lg);
}

/* Sidebar navigation */
[data-testid="stSidebar"] .nav-item {
  border-radius: var(--apple-radius-small);
  padding: var(--apple-space-sm) var(--apple-space-md);
  margin: var(--apple-space-xs) 0;
  transition: all var(--apple-transition-fast);
}

[data-testid="stSidebar"] .nav-item:hover {
  background-color: rgba(0, 0, 0, 0.03);
}

/* Radio buttons in sidebar */
[data-testid="stSidebar"] .stRadio label {
  font-size: var(--apple-text-callout);
  color: var(--apple-text-primary);
  padding: var(--apple-space-sm) 0;
  cursor: pointer;
}

[data-testid="stSidebar"] .stRadio input[type="radio"] {
  accent-color: var(--apple-accent-blue);
}

/* Checkboxes in sidebar */
[data-testid="stSidebar"] .stCheckbox label {
  font-size: var(--apple-text-callout);
  color: var(--apple-text-primary);
}

[data-testid="stSidebar"] .stCheckbox input[type="checkbox"] {
  accent-color: var(--apple-success);
  width: 18px;
  height: 18px;
}

/* Sidebar section dividers */
[data-testid="stSidebar"] hr {
  border: none;
  height: 1px;
  background-color: var(--apple-separator);
  margin: var(--apple-space-md) 0;
}

/* Sidebar headers */
[data-testid="stSidebar"] h3 {
  font-size: var(--apple-text-headline);
  font-weight: var(--apple-weight-semibold);
  color: var(--apple-text-primary);
  margin-bottom: var(--apple-space-sm);
}

/* Expander in sidebar */
[data-testid="stSidebar"] .streamlit-expanderHeader {
  font-size: var(--apple-text-callout);
  font-weight: var(--apple-weight-semibold);
  color: var(--apple-text-primary);
  padding: var(--apple-space-sm) 0;
}

[data-testid="stSidebar"] .streamlit-expanderContent {
  padding: var(--apple-space-sm) 0;
}

/* --------------------------------------------
   PROGRESS BAR
   -------------------------------------------- */

/* Progress bar container */
.stProgress {
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: var(--apple-radius-full);
  height: 6px;
  overflow: hidden;
}

/* Progress bar fill */
.stProgress > div {
  background-color: var(--apple-success);
  border-radius: var(--apple-radius-full);
  transition: width var(--apple-transition-slow);
  height: 100%;
}

/* Progress bar with different colors */
.stProgress.success > div {
  background-color: var(--apple-success);
}

.stProgress.warning > div {
  background-color: var(--apple-warning);
}

.stProgress.error > div {
  background-color: var(--apple-error);
}

.stProgress.info > div {
  background-color: var(--apple-accent-blue);
}

/* --------------------------------------------
   EXPANDERS
   -------------------------------------------- */

/* Expander container */
.streamlit-expander {
  background-color: var(--apple-bg-card);
  border-radius: var(--apple-radius-large);
  box-shadow: var(--apple-shadow-card);
  margin-bottom: var(--apple-space-md);
}

/* Expander header */
.streamlit-expanderHeader {
  font-size: var(--apple-text-body);
  font-weight: var(--apple-weight-semibold);
  color: var(--apple-text-primary);
  padding: var(--apple-space-md);
  cursor: pointer;
  border-radius: var(--apple-radius-large);
  transition: all var(--apple-transition-fast);
}

.streamlit-expanderHeader:hover {
  background-color: rgba(0, 0, 0, 0.02);
}

/* Expander content */
.streamlit-expanderContent {
  padding: var(--apple-space-md);
  border-top: 1px solid var(--apple-border);
}

/* --------------------------------------------
   TABS
   -------------------------------------------- */

/* Tabs container */
.stTabs {
  background-color: transparent;
}

/* Tab buttons */
.stTabs [data-baseweb="tab-list"] {
  border-bottom: 1px solid var(--apple-border);
}

.stTabs [data-baseweb="tab"] {
  font-size: var(--apple-text-callout);
  font-weight: var(--apple-weight-medium);
  color: var(--apple-text-secondary);
  padding: var(--apple-space-sm) var(--apple-space-md);
  border: none;
  background: transparent;
  transition: all var(--apple-transition-fast);
}

.stTabs [data-baseweb="tab"]:hover {
  color: var(--apple-text-primary);
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
  color: var(--apple-accent-blue);
  border-bottom: 2px solid var(--apple-accent-blue);
}

/* Tab content */
.stTabs [data-baseweb="tab-panel"] {
  padding: var(--apple-space-lg) 0;
}

/* --------------------------------------------
   ALERTS & NOTIFICATIONS
   -------------------------------------------- */

/* Success alert */
.stAlert.success {
  background-color: rgba(52, 199, 89, 0.08);
  border: 1px solid rgba(52, 199, 89, 0.2);
  border-radius: var(--apple-radius-medium);
  padding: var(--apple-space-md);
  color: #1D6B2B;
}

/* Info alert */
.stAlert.info {
  background-color: rgba(0, 122, 255, 0.08);
  border: 1px solid rgba(0, 122, 255, 0.2);
  border-radius: var(--apple-radius-medium);
  padding: var(--apple-space-md);
  color: #004499;
}

/* Warning alert */
.stAlert.warning {
  background-color: rgba(255, 149, 0, 0.08);
  border: 1px solid rgba(255, 149, 0, 0.2);
  border-radius: var(--apple-radius-medium);
  padding: var(--apple-space-md);
  color: #995C00;
}

/* Error alert */
.stAlert.error {
  background-color: rgba(255, 59, 48, 0.08);
  border: 1px solid rgba(255, 59, 48, 0.2);
  border-radius: var(--apple-radius-medium);
  padding: var(--apple-space-md);
  color: #991D15;
}

/* --------------------------------------------
   SLIDERS
   -------------------------------------------- */

/* Slider container */
.stSlider {
  padding: var(--apple-space-sm) 0;
}

/* Slider track */
.stSlider [data-testid="stTickBar"] {
  background-color: var(--apple-border);
}

/* Slider filled track */
.stSlider [data-testid="stThumbValue"] {
  background-color: var(--apple-success);
}

/* Slider thumb */
.stSlider [role="slider"] {
  background-color: var(--apple-bg-card);
  border: 2px solid var(--apple-success);
  box-shadow: var(--apple-shadow-button);
  width: 20px;
  height: 20px;
  border-radius: 50%;
}

.stSlider [role="slider"]:hover {
  transform: scale(1.1);
}

/* --------------------------------------------
   DATAFRAMES / TABLES
   -------------------------------------------- */

/* Dataframe container */
.stDataFrame {
  border-radius: var(--apple-radius-large);
  box-shadow: var(--apple-shadow-card);
  overflow: hidden;
}

.stDataFrame table {
  font-family: var(--apple-font-family);
  font-size: var(--apple-text-callout);
}

.stDataFrame th {
  background-color: #F5F5F7;
  font-weight: var(--apple-weight-semibold);
  color: var(--apple-text-primary);
  padding: var(--apple-space-sm) var(--apple-space-md);
}

.stDataFrame td {
  padding: var(--apple-space-sm) var(--apple-space-md);
  color: var(--apple-text-primary);
}

.stDataFrame tr:hover td {
  background-color: rgba(0, 0, 0, 0.02);
}

/* --------------------------------------------
   CONTAINERS & LAYOUT
   -------------------------------------------- */

/* Section container */
.apple-section {
  padding: var(--apple-space-xxl) 0;
}

/* Container with proper spacing */
.apple-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--apple-space-lg);
}

/* Grid gaps */
.apple-grid {
  display: grid;
  gap: var(--apple-space-lg);
}

/* Flex container */
.apple-flex {
  display: flex;
  gap: var(--apple-space-md);
}

/* Stack vertical */
.apple-stack {
  display: flex;
  flex-direction: column;
  gap: var(--apple-space-md);
}

/* Separator line */
.apple-separator {
  height: 1px;
  background-color: var(--apple-separator);
  margin: var(--apple-space-lg) 0;
}

/* --------------------------------------------
   TYPOGRAPHY OVERRIDES
   -------------------------------------------- */

/* Headings */
h1 {
  font-size: var(--apple-text-large-title);
  font-weight: var(--apple-weight-bold);
  color: var(--apple-text-primary);
  letter-spacing: var(--apple-letter-spacing-tight);
  line-height: var(--apple-line-height-tight);
  margin-bottom: var(--apple-space-lg);
}

h2 {
  font-size: var(--apple-text-title);
  font-weight: var(--apple-weight-semibold);
  color: var(--apple-text-primary);
  letter-spacing: var(--apple-letter-spacing-tight);
  line-height: var(--apple-line-height-tight);
  margin-bottom: var(--apple-space-md);
}

h3 {
  font-size: var(--apple-text-headline);
  font-weight: var(--apple-weight-semibold);
  color: var(--apple-text-primary);
  line-height: var(--apple-line-height-tight);
  margin-bottom: var(--apple-space-sm);
}

/* Paragraph */
p {
  font-size: var(--apple-text-body);
  color: var(--apple-text-primary);
  line-height: var(--apple-line-height-normal);
  margin-bottom: var(--apple-space-md);
}

/* Caption */
.caption {
  font-size: var(--apple-text-footnote);
  color: var(--apple-text-tertiary);
}

/* --------------------------------------------
   ANIMATIONS
   -------------------------------------------- */

/* Fade in animation */
@keyframes apple-fade-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.apple-fade-in {
  animation: apple-fade-in var(--apple-transition-normal) ease forwards;
}

/* Staggered reveal for multiple items */
.apple-stagger-1 { animation-delay: 0ms; }
.apple-stagger-2 { animation-delay: 50ms; }
.apple-stagger-3 { animation-delay: 100ms; }
.apple-stagger-4 { animation-delay: 150ms; }
.apple-stagger-5 { animation-delay: 200ms; }

/* Pulse animation for loading states */
@keyframes apple-pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.apple-pulse {
  animation: apple-pulse 2s ease-in-out infinite;
}

/* --------------------------------------------
   UTILITY CLASSES FOR STREAMLIT
   -------------------------------------------- */

/* Hide Streamlit branding */
#MainMenu, header, footer {
  visibility: hidden;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--apple-bg-primary);
}

::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: var(--apple-radius-full);
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

/* Loading spinner */
.stSpinner > div {
  border-color: var(--apple-success);
}

/* Toast notifications */
[data-testid="stToast"] {
  border-radius: var(--apple-radius-large);
  box-shadow: var(--apple-shadow-modal);
  padding: var(--apple-space-md);
}
"""

APPLE_COMPONENTS_CSS = APPLE_DESIGN_TOKENS + _COMPONENT_CSS

__all__ = ["APPLE_COMPONENTS_CSS"]
