import streamlit as st
import json
from typing import Dict, Any, Optional
from functools import lru_cache
import time

class AnimationManager:
    def __init__(self):
        self._animations: Dict[str, Dict[str, Any]] = {}
        self._last_animation_time: Dict[str, float] = {}
        self._animation_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 3600  # 1 hour cache TTL

    @lru_cache(maxsize=32)
    def load_animation(self, path: str) -> Dict[str, Any]:
        """Load and cache animation data"""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading animation {path}: {str(e)}")
            return {}

    def get_animation(self, path: str) -> Dict[str, Any]:
        """Get animation with caching"""
        current_time = time.time()
        if path in self._animation_cache:
            cache_time = self._last_animation_time.get(path, 0)
            if current_time - cache_time < self._cache_ttl:
                return self._animation_cache[path]

        animation_data = self.load_animation(path)
        self._animation_cache[path] = animation_data
        self._last_animation_time[path] = current_time
        return animation_data

    def display_animation(self, path: str, height: int = 200, key: Optional[str] = None) -> None:
        """Display animation with performance optimizations"""
        try:
            animation_data = self.get_animation(path)
            if animation_data:
                st.markdown(
                    f"""
                    <div style="height:{height}px; display:flex; align-items:center; justify-content:center; 
                    background:rgba(72,149,239,0.1); border-radius:8px; margin:10px 0;">
                        <div style="text-align:center;">
                            <div style="font-size:24px; margin-bottom:10px;">🔄</div>
                            <div>Animation placeholder</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        except Exception as e:
            print(f"Error displaying animation {path}: {str(e)}")

    def preload_animations(self, paths: list[str]) -> None:
        """Preload animations to reduce stuttering"""
        for path in paths:
            self.get_animation(path)

# Global animation manager
animation_manager = AnimationManager()

def staggered_animation(index: int, base_delay: float = 0.1, max_delay: float = 1.0) -> float:
    """
    Calculate staggered animation delay based on index
    
    Args:
        index: The index of the element in a sequence
        base_delay: The base delay between each element (in seconds)
        max_delay: Maximum delay cap to prevent excessive delays
        
    Returns:
        The calculated delay in seconds
    """
    delay = min(index * base_delay, max_delay)
    return round(delay, 2)

def apply_staggered_animations() -> None:
    """Apply staggered animations to elements with data-stagger attribute"""
    st.markdown("""
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        // Add animation-ready class to body when DOM is loaded
        document.body.classList.add('animation-ready');
        
        // Apply staggered animation delays
        const staggeredElements = document.querySelectorAll('[data-stagger]');
        staggeredElements.forEach((el, index) => {
            const delay = Math.min(index * 0.1, 1.0);
            el.style.animationDelay = `${delay}s`;
            el.style.transitionDelay = `${delay}s`;
        });
    });
    </script>
    """, unsafe_allow_html=True)

def smooth_transition(duration: float = 0.3) -> None:
    """Add smooth transition effect"""
    st.markdown(f"""
        <style>
            .stApp {{
                transition: all {duration}s ease-in-out;
            }}
        </style>
    """, unsafe_allow_html=True)

def fade_in(element: Any, duration: float = 0.5) -> None:
    """Add fade-in effect to an element"""
    st.markdown(f"""
        <style>
            .fade-in {{
                animation: fadeIn {duration}s;
            }}
            @keyframes fadeIn {{
                0% {{ opacity: 0; }}
                100% {{ opacity: 1; }}
            }}
        </style>
    """, unsafe_allow_html=True)
    st.markdown(f'<div class="fade-in">{element}</div>', unsafe_allow_html=True)

def slide_in(element: Any, direction: str = "left", duration: float = 0.5) -> None:
    """Add slide-in effect to an element"""
    st.markdown(f"""
        <style>
            .slide-in-{direction} {{
                animation: slideIn{direction.capitalize()} {duration}s;
            }}
            @keyframes slideInLeft {{
                0% {{ transform: translateX(-100%); opacity: 0; }}
                100% {{ transform: translateX(0); opacity: 1; }}
            }}
            @keyframes slideInRight {{
                0% {{ transform: translateX(100%); opacity: 0; }}
                100% {{ transform: translateX(0); opacity: 1; }}
            }}
            @keyframes slideInUp {{
                0% {{ transform: translateY(100%); opacity: 0; }}
                100% {{ transform: translateY(0); opacity: 1; }}
            }}
            @keyframes slideInDown {{
                0% {{ transform: translateY(-100%); opacity: 0; }}
                100% {{ transform: translateY(0); opacity: 1; }}
            }}
        </style>
    """, unsafe_allow_html=True)
    st.markdown(f'<div class="slide-in-{direction}">{element}</div>', unsafe_allow_html=True)

def pulse(element: Any, duration: float = 1.0) -> None:
    """Add pulse effect to an element"""
    st.markdown(f"""
        <style>
            .pulse {{
                animation: pulse {duration}s infinite;
            }}
            @keyframes pulse {{
                0% {{ transform: scale(1); }}
                50% {{ transform: scale(1.05); }}
                100% {{ transform: scale(1); }}
            }}
        </style>
    """, unsafe_allow_html=True)
    st.markdown(f'<div class="pulse">{element}</div>', unsafe_allow_html=True)

def optimize_animations() -> None:
    """Optimize animation performance"""
    st.markdown("""
        <style>
            * {
                will-change: transform, opacity;
                backface-visibility: hidden;
                transform: translateZ(0);
            }
            .stApp {
                overflow-x: hidden;
            }
            
            /* Staggered animation base styles */
            .animation-ready [data-stagger] {
                opacity: 0;
                animation-fill-mode: forwards;
            }
            
            .animation-ready [data-stagger].stagger-fade-in {
                animation-name: fadeIn;
                animation-duration: 0.5s;
            }
            
            .animation-ready [data-stagger].stagger-slide-in-left {
                animation-name: slideInLeft;
                animation-duration: 0.5s;
            }
            
            .animation-ready [data-stagger].stagger-slide-in-right {
                animation-name: slideInRight;
                animation-duration: 0.5s;
            }
            
            .animation-ready [data-stagger].stagger-slide-in-up {
                animation-name: slideInUp;
                animation-duration: 0.5s;
            }
        </style>
    """, unsafe_allow_html=True) 