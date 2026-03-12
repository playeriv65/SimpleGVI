"""
Apple Animations System for SimpleGVI Streamlit App
Apple-style CSS animations with subtle, purposeful motion.
"""

# Apple Design Language CSS Animations
# Timing: 0.2-0.3s for micro-interactions, 0.4s for page-level animations
APPLE_ANIMATIONS_CSS = """
/* ============================================
   APPLE ANIMATIONS SYSTEM
   Subtle, purposeful motion for enhanced UX
   ============================================ */

/* ============================================
   KEYFRAME DEFINITIONS
   ============================================ */

/* Fade In Up - Primary page entrance */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Fade In with Scale - Card entrance */
@keyframes fadeInScale {
  from {
    opacity: 0;
    transform: scale(0.98) translateY(8px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* Simple Fade In */
@keyframes simpleFadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* Fade Out */
@keyframes simpleFadeOut {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}

/* Apple Spinner - Rotating segments */
@keyframes appleSpin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* Spinner Segment Animation */
@keyframes spinPulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* Progress Pulse */
@keyframes progressPulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.85;
  }
}

/* Subtle Bounce - Spring animation */
@keyframes subtleBounce {
  0% {
    transform: scale(1);
  }
  40% {
    transform: scale(0.97);
  }
  80% {
    transform: scale(1.02);
  }
  100% {
    transform: scale(1);
  }
}

/* Spring Pop */
@keyframes springPop {
  0% {
    transform: scale(0.95);
  }
  60% {
    transform: scale(1.02);
  }
  100% {
    transform: scale(1);
  }
}

/* Shimmer Effect */
@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

/* ============================================
   PAGE LOAD ANIMATIONS
   Staggered fade-in for sequential reveals
   ============================================ */

.page-load-item {
  opacity: 0;
  animation: fadeInUp 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
}

.page-load-item:nth-child(1) { animation-delay: 0s; }
.page-load-item:nth-child(2) { animation-delay: 0.1s; }
.page-load-item:nth-child(3) { animation-delay: 0.2s; }
.page-load-item:nth-child(4) { animation-delay: 0.3s; }
.page-load-item:nth-child(5) { animation-delay: 0.4s; }
.page-load-item:nth-child(6) { animation-delay: 0.5s; }
.page-load-item:nth-child(7) { animation-delay: 0.6s; }
.page-load-item:nth-child(8) { animation-delay: 0.7s; }

/* ============================================
   CARD ENTRANCE ANIMATIONS
   ============================================ */

.fade-in-up {
  opacity: 0;
  animation: fadeInScale 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
}

/* Staggered card delays */
.card-stagger-1 { animation-delay: 0.1s; }
.card-stagger-2 { animation-delay: 0.2s; }
.card-stagger-3 { animation-delay: 0.3s; }
.card-stagger-4 { animation-delay: 0.4s; }
.card-stagger-5 { animation-delay: 0.5s; }
.card-stagger-6 { animation-delay: 0.6s; }

/* ============================================
   HOVER EFFECTS
   ============================================ */

/* Card Hover - Subtle lift with shadow */
.card-hover {
  transition: transform 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94),
              box-shadow 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  will-change: transform, box-shadow;
}

.card-hover:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12),
              0 2px 8px rgba(0, 0, 0, 0.08);
}

/* Button Hover - Micro lift */
.btn-hover {
  transition: transform 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94),
              background-color 0.2s ease,
              box-shadow 0.2s ease;
  will-change: transform;
}

.btn-hover:hover {
  transform: translateY(-1px);
}

.btn-hover:active {
  transform: translateY(0);
  transition-duration: 0.1s;
}

/* Interactive Element Hover */
.interactive-hover {
  transition: opacity 0.2s ease,
              transform 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.interactive-hover:hover {
  opacity: 0.8;
  transform: scale(1.02);
}

/* ============================================
   LOADING SPINNER
   Apple-style rotating segments
   ============================================ */

.apple-spinner {
  position: relative;
  width: 24px;
  height: 24px;
}

.apple-spinner::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-right-color: currentColor;
  animation: appleSpin 0.8s linear infinite;
}

/* Thin Stroke Spinner */
.apple-spinner-thin {
  width: 20px;
  height: 20px;
  border: 1.5px solid rgba(0, 0, 0, 0.1);
  border-top-color: currentColor;
  border-radius: 50%;
  animation: appleSpin 0.8s linear infinite;
}

/* Larger Spinner */
.apple-spinner-lg {
  width: 32px;
  height: 32px;
  border-width: 2px;
}

/* Spinner with pulse effect */
.apple-spinner-pulse {
  animation: appleSpin 0.8s linear infinite, spinPulse 1.5s ease-in-out infinite;
}

/* ============================================
   PROGRESS ANIMATION
   ============================================ */

.apple-progress {
  position: relative;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.08);
}

.apple-progress-bar {
  height: 100%;
  border-radius: 999px;
  transition: width 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  animation: progressPulse 2s ease-in-out infinite;
  will-change: width;
}

/* Smooth width transition utility */
.progress-smooth {
  transition: width 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

/* ============================================
   FADE TRANSITIONS
   ============================================ */

.apple-fade-in {
  opacity: 0;
  animation: simpleFadeIn 0.3s ease forwards;
}

.apple-fade-out {
  opacity: 1;
  animation: simpleFadeOut 0.3s ease forwards;
}

/* Fade with display toggle */
.apple-fade-visible {
  opacity: 1;
  transition: opacity 0.3s ease;
}

.apple-fade-hidden {
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s ease;
}

/* ============================================
   SPRING ANIMATIONS
   ============================================ */

/* Subtle bounce on interaction */
.spring-bounce {
  animation: subtleBounce 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

/* Pop animation for buttons/elements */
.spring-pop {
  animation: springPop 0.35s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

/* Spring hover effect */
.spring-hover {
  transition: transform 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.spring-hover:hover {
  transform: scale(1.05);
}

.spring-hover:active {
  transform: scale(0.98);
  transition-duration: 0.1s;
}

/* ============================================
   UTILITY CLASSES
   ============================================ */

/* Animation timing utilities */
.duration-fast { animation-duration: 0.2s; }
.duration-normal { animation-duration: 0.3s; }
.duration-slow { animation-duration: 0.4s; }
.duration-slower { animation-duration: 0.6s; }

/* Animation fill modes */
.fill-forwards { animation-fill-mode: forwards; }
.fill-backwards { animation-fill-mode: backwards; }
.fill-both { animation-fill-mode: both; }

/* Animation play state */
.animate-pause { animation-play-state: paused; }
.animate-running { animation-play-state: running; }

/* Easing curves */
.ease-apple { animation-timing-function: cubic-bezier(0.25, 0.46, 0.45, 0.94); }
.ease-spring { animation-timing-function: cubic-bezier(0.68, -0.55, 0.265, 1.55); }
.ease-out-expo { animation-timing-function: cubic-bezier(0.19, 1, 0.22, 1); }

/* Transform utilities */
.translate-up-2 { transform: translateY(-2px); }
.translate-up-4 { transform: translateY(-4px); }
.scale-98 { transform: scale(0.98); }
.scale-102 { transform: scale(1.02); }

/* ============================================
   SKELETON/LOADING SHIMMER
   ============================================ */

.skeleton-shimmer {
  background: linear-gradient(
    90deg,
    rgba(0, 0, 0, 0.06) 25%,
    rgba(0, 0, 0, 0.12) 50%,
    rgba(0, 0, 0, 0.06) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

/* ============================================
   ACCESSIBILITY: REDUCED MOTION
   Respect user preferences for less motion
   ============================================ */

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
  
  .page-load-item,
  .fade-in-up,
  .apple-fade-in {
    opacity: 1;
    animation: none;
    transform: none;
  }
  
  .apple-spinner,
  .apple-spinner-thin {
    animation: none;
    opacity: 0.5;
  }
  
  .skeleton-shimmer {
    animation: none;
    background: rgba(0, 0, 0, 0.08);
  }
  
  .apple-progress-bar {
    animation: none;
  }
  
  .card-hover:hover,
  .btn-hover:hover,
  .interactive-hover:hover,
  .spring-hover:hover {
    transform: none;
  }
}

/* ============================================
   PERFORMANCE OPTIMIZATIONS
   ============================================ */

/* GPU acceleration hints */
.will-animate {
  will-change: transform, opacity;
}

/* Contain paint for animated elements */
.animate-container {
  contain: layout style paint;
}

/* Disable animations on battery saver */
@media (prefers-reduced-motion: reduce), (update: slow) {
  .page-load-item,
  .fade-in-up,
  .apple-spinner,
  .skeleton-shimmer {
    animation: none !important;
  }
}
"""

# Export for use in other modules
__all__ = ["APPLE_ANIMATIONS_CSS"]


if __name__ == "__main__":
    # Quick validation that CSS is properly formatted
    print(f"Apple Animations CSS loaded successfully!")
    print(f"Total characters: {len(APPLE_ANIMATIONS_CSS):,}")
    print(
        f"Contains reduced-motion support: {'prefers-reduced-motion' in APPLE_ANIMATIONS_CSS}"
    )
    print(
        f"Contains keyframes: {APPLE_ANIMATIONS_CSS.count('@keyframes')} keyframe definitions"
    )
