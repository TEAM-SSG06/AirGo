"""
Smooth Human Mouse Kinematics for Patchright.
Combines Cubic Bezier curves, Fitts's Law overshoot corrections, Gaussian micro-jitter,
and inertia-based smooth scrolling to simulate authentic human biometric interactions for Akamai Bot Manager bypass.
"""

import math
import random
import asyncio
from typing import Tuple, List, Dict, Optional, Union, Any


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b."""
    return a + (b - a) * t


def cubic_bezier(
    t: float,
    p0: Tuple[float, float],
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float]
) -> Tuple[float, float]:
    """Evaluates a cubic Bezier curve at parameter t in [0, 1]."""
    u = 1.0 - t
    tt = t * t
    uu = u * u
    uuu = uu * u
    ttt = tt * t

    x = uuu * p0[0] + 3 * uu * t * p1[0] + 3 * u * tt * p2[0] + ttt * p3[0]
    y = uuu * p0[1] + 3 * uu * t * p1[1] + 3 * u * tt * p2[1] + ttt * p3[1]
    return (x, y)


def generate_bezier_path(
    start: Tuple[float, float],
    target: Tuple[float, float],
    steps: int = 35,
    deviation_factor: float = 0.25
) -> List[Tuple[float, float]]:
    """
    Generates a curved human-like Bezier path between start and target points
    with realistic lateral deviation.
    """
    dx = target[0] - start[0]
    dy = target[1] - start[1]
    dist = math.hypot(dx, dy)

    # Lateral deviation proportional to distance, capped reasonably
    max_dev = min(80.0, max(15.0, dist * deviation_factor))

    # Control points with perpendicular displacement
    p1 = (
        lerp(start[0], target[0], 0.33) + random.uniform(-max_dev, max_dev),
        lerp(start[1], target[1], 0.33) + random.uniform(-max_dev, max_dev)
    )
    p2 = (
        lerp(start[0], target[0], 0.66) + random.uniform(-max_dev, max_dev),
        lerp(start[1], target[1], 0.66) + random.uniform(-max_dev, max_dev)
    )

    return [cubic_bezier(i / max(1, steps - 1), start, p1, p2, target) for i in range(steps)]


class HumanMouse:
    """
    High-fidelity human mouse controller designed for Patchright automation.
    Combines Cubic Bezier curves, Fitts's Law overshoot corrections, Gaussian micro-jitter,
    and visual cursor tracking for audit ground-truth.
    """

    def __init__(self, page: Any):
        self.page = page
        self.current_x: float = random.uniform(300, 700)
        self.current_y: float = random.uniform(200, 500)
        self._cursor_shown: bool = False

    async def show_cursor(self):
        """Displays a red dot tracker on the page to provide visual ground truth."""
        try:
            await self.page.evaluate('''() => {
                if (window._mmt_red_dot_active) return;
                window._mmt_red_dot_active = true;
                let dot = document.createElement("div");
                dot.id = "_mmt_audit_cursor";
                dot.style.position = "fixed";
                dot.style.width = "7px";
                dot.style.height = "7px";
                dot.style.borderRadius = "50%";
                dot.style.backgroundColor = "red";
                dot.style.boxShadow = "0 0 4px 1px rgba(255, 0, 0, 0.7)";
                dot.style.zIndex = "9999999";
                dot.style.pointerEvents = "none";
                dot.style.transition = "transform 0.05s ease-out";
                document.body.appendChild(dot);

                document.addEventListener("mousemove", (e) => {
                    dot.style.left = e.clientX + "px";
                    dot.style.top = e.clientY + "px";
                });
            }''')
            self._cursor_shown = True
        except Exception:
            pass

    async def get_element_center(self, locator_or_element: Any) -> Tuple[float, float]:
        """
        Retrieves bounding box and returns a point slightly randomized within the element center.
        """
        if hasattr(locator_or_element, "bounding_box"):
            box = await locator_or_element.bounding_box()
        elif hasattr(locator_or_element, "element_handle"):
            h = await locator_or_element.element_handle()
            box = await h.bounding_box() if h else None
        else:
            box = None

        if not box:
            raise ValueError(f"Could not retrieve bounding box for {locator_or_element}")

        # Target center with slight human variance (within middle 60% of element)
        x_min = box["x"] + box["width"] * 0.2
        x_max = box["x"] + box["width"] * 0.8
        y_min = box["y"] + box["height"] * 0.2
        y_max = box["y"] + box["height"] * 0.8

        return (random.uniform(x_min, x_max), random.uniform(y_min, y_max))

    async def move_to(
        self,
        target: Union[Tuple[float, float], Any],
        steps: Optional[int] = None,
        overshoot: bool = True
    ) -> Tuple[float, float]:
        """
        Smoothly moves the cursor along a Bezier curve to the target coordinates or element,
        incorporating natural micro-jitter and optional overshoot correction.
        """
        if isinstance(target, (tuple, list)):
            target_x, target_y = float(target[0]), float(target[1])
        else:
            target_x, target_y = await self.get_element_center(target)

        start_point = (self.current_x, self.current_y)
        dist = math.hypot(target_x - self.current_x, target_y - self.current_y)

        if steps is None:
            # Scale steps with distance: 20 steps minimum, up to 60 for large distances
            steps = int(max(20, min(65, dist / 15)))

        # 1. Optional subtle overshoot past target
        if overshoot and dist > 120 and random.random() < 0.65:
            overshoot_factor = random.uniform(1.03, 1.08)
            overshoot_x = start_point[0] + (target_x - start_point[0]) * overshoot_factor
            overshoot_y = start_point[1] + (target_y - start_point[1]) * overshoot_factor

            # Path to overshoot point
            first_path = generate_bezier_path(start_point, (overshoot_x, overshoot_y), steps=int(steps * 0.8))
            for x, y in first_path:
                jx = x + random.gauss(0, 0.6)
                jy = y + random.gauss(0, 0.6)
                await self.page.mouse.move(jx, jy)
                await asyncio.sleep(random.uniform(0.003, 0.009))

            # Correction to exact target
            correction_path = generate_bezier_path((overshoot_x, overshoot_y), (target_x, target_y), steps=random.randint(8, 14))
            for x, y in correction_path:
                await self.page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.005, 0.012))

        else:
            # Direct Bezier path
            path = generate_bezier_path(start_point, (target_x, target_y), steps=steps)
            for x, y in path:
                jx = x + random.gauss(0, 0.5)
                jy = y + random.gauss(0, 0.5)
                await self.page.mouse.move(jx, jy)
                await asyncio.sleep(random.uniform(0.004, 0.010))

        self.current_x = target_x
        self.current_y = target_y
        return (target_x, target_y)

    async def click_at(
        self,
        target: Union[Tuple[float, float], Any],
        dwell_before_click: float = 0.15,
        click_delay_ms: Optional[float] = None
    ):
        """
        Moves cursor to target and clicks with authentic human dwell and button hold times.
        """
        await self.move_to(target)
        await asyncio.sleep(dwell_before_click + random.uniform(0.05, 0.15))

        hold_time = click_delay_ms or random.uniform(65, 130)
        await self.page.mouse.down()
        await asyncio.sleep(hold_time / 1000.0)
        await self.page.mouse.up()
        await asyncio.sleep(random.uniform(0.05, 0.15))

    async def smooth_scroll(
        self,
        delta_y: int,
        steps: int = 15,
        pause_between: float = 0.03
    ):
        """
        Simulates natural mouse wheel inertia scrolling with acceleration and deceleration.
        """
        if steps <= 0:
            steps = 10

        # Create inertia velocity bell curve
        weights = [math.sin(math.pi * (i + 1) / (steps + 1)) for i in range(steps)]
        weight_sum = sum(weights)

        for w in weights:
            step_delta = (w / weight_sum) * delta_y
            await self.page.mouse.wheel(0, step_delta)
            await asyncio.sleep(pause_between + random.uniform(-0.005, 0.008))

        await asyncio.sleep(random.uniform(0.2, 0.4))

    async def human_hover(self, target: Any, dwell_sec: float = 1.0):
        """Hovers over an element for a given duration with subtle organic micro-movements."""
        import time
        tx, ty = await self.move_to(target)
        end_time = time.monotonic() + dwell_sec
        while time.monotonic() < end_time:
            # subtle jitter around the hovered element
            jx = tx + random.gauss(0, 1.2)
            jy = ty + random.gauss(0, 1.2)
            await self.page.mouse.move(jx, jy)
            await asyncio.sleep(random.uniform(0.15, 0.35))
