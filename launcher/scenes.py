"""Original terminal artwork and an independent, deterministic scene player."""

from dataclasses import dataclass
import math
import random


@dataclass(frozen=True)
class Scene:
    id: str
    title: str
    description: str
    duration: float
    loop: bool = False


SCENES = (
    Scene("orbit", "Moon orbit", "Arzi circles a cratered Moon under a drifting starfield.", 18, True),
    Scene("descent", "Powered descent", "Approach Tranquility with the engine burning and Earth above.", 18),
    Scene("landing", "Touchdown", "A close landing, fluttering flame, and settling lunar dust.", 12),
    Scene("liftoff", "Arzi liftoff", "Ignition, a cloud of dust, and a climb back into the stars.", 14),
    Scene("moonwalk", "First footsteps", "An astronaut plants the Lebanese flag, salutes, and returns aboard.", 16),
    Scene("moonhop", "Moon hop", "Jump blocks, collect stars, raise the Lebanese flag, and board Arzi.", 18),
)
_rng = random.Random(11)
_STARS = tuple((_rng.random(), _rng.random(), _rng.choice("..+*")) for _ in range(70))


class Canvas:
    """A clipped terminal frame; runs merge neighboring cells of the same color."""

    def __init__(self, width, height):
        if width < 1 or height < 1:
            raise ValueError("A scene needs a positive stage size")
        self.width, self.height = width, height
        self.cells = [[(" ", "normal") for _ in range(width)] for _ in range(height)]

    def text(self, x, y, text, style="normal"):
        if 0 <= y < self.height:
            for offset, char in enumerate(text):
                if 0 <= x + offset < self.width:
                    self.cells[y][x + offset] = (char, style)

    def art(self, x, y, lines, style="normal"):
        for row, line in enumerate(lines):
            self.text(x, y + row, line, style)

    def pixel(self, x, y, color):
        x, y = round(x), round(y)
        row, half = divmod(y, 2)
        if 0 <= x < self.width and 0 <= row < self.height:
            char, style = self.cells[row][x]
            top, bottom = style.split(":")[1:] if style.startswith("pixel:") else ("space", "space")
            if half:
                bottom = color
            else:
                top = color
            self.cells[row][x] = ("▀", f"pixel:{top}:{bottom}")

    def sprite(self, x, y, lines, colors):
        for dy, line in enumerate(lines):
            for dx, char in enumerate(line):
                if char in colors:
                    self.pixel(x + dx, y + dy, colors[char])

    def runs(self):
        for y, row in enumerate(self.cells):
            start = 0
            for x in range(1, self.width + 1):
                if x == self.width or row[x][1] != row[start][1]:
                    yield start, y, "".join(char for char, _ in row[start:x]), row[start][1]
                    start = x

    def plain(self):
        return "\n".join("".join(char for char, _ in row) for row in self.cells)


def smooth(value):
    return value * value * (3 - 2 * value)


PIXEL_COLORS = {
    "space": (234, 0), "white": (231, 7), "metal": (250, 7),
    "shade": (240, 0), "gold": (220, 3), "red": (160, 1),
    "green": (28, 2), "blue": (25, 4), "cyan": (117, 6),
    "flame": (203, 1),
}
FLAG_PIXELS = (
    "rrrrrrrrrrrr", "rrrrrrrrrrrr",
    "wwwwwggwwwww", "wwwwggggwwww", "wwwggggggwww", "wwwwwggwwwww",
    "rrrrrrrrrrrr", "rrrrrrrrrrrr",
)
SHIP_PIXELS = (
    "          w          ", "          s          ",
    "        ssWss        ", "      ssWWWWWss      ",
    "     sWWcWWcWWs      ", "     sWccWWccWs      ",
    "     sWWWWWWWWs      ", "      sWWssWWs       ",
    "     sGGGGGGGGs      ", "    sGGgGGgGGGGs     ",
    "   sGGGGgGGgGGGGs    ", "    ssGGGGGGGGss     ",
    "   ss    ss    ss    ", "  ss            ss   ",
    "ssss            ssss ",
)
_SPRITE_COLORS = {"w": "white", "W": "metal", "s": "shade", "G": "gold", "g": "shade", "c": "cyan"}


def sky(frame, seconds, horizon=None):
    horizon = frame.height if horizon is None else horizon
    phase = seconds / SCENES[0].duration * 2 * math.pi
    for i, (sx, sy, glyph) in enumerate(_STARS):
        drift = math.sin(phase) * (0.7 + i % 3)
        x = round((sx * (frame.width - 1) + drift) % frame.width)
        y = round(sy * max(1, horizon - 2))
        shimmer = math.sin(phase * (1 + i % 3) + i * 1.7)
        frame.text(x, y, "+" if shimmer > 0.8 and glyph == "*" else glyph,
                   "cyan" if shimmer > 0.6 else "dim")


def surface(frame, ground):
    for x in range(frame.width):
        frame.pixel(x, ground * 2, "metal")
        if (x * 7) % 17 < 3:
            frame.pixel(x, ground * 2 + 1, "shade")
    for center, radius in [(frame.width // 5, 4), (frame.width * 3 // 4, 7)]:
        for x in range(-radius, radius + 1):
            y = ground * 2 + 1 + round(1.3 * (1 - (x / radius) ** 2))
            frame.pixel(center + x, y, "shade")


def earth(frame):
    cx, cy = frame.width - 8, 4
    for y in range(-3, 4):
        for x in range(-3, 4):
            if x * x + y * y <= 10:
                color = "blue" if x > 1 else "cyan"
                if (x * 2 + y * 3) % 9 < 3:
                    color = "green"
                if (y * 7 - x) % 11 < 2:
                    color = "white"
                frame.pixel(cx + x, cy + y, color)


def lander(frame, x, y, boarded=False):
    frame.sprite(round(x), round(y), SHIP_PIXELS, _SPRITE_COLORS)
    frame.text(round(x) + 8, (round(y) + 6) // 2, "ARZI", "pixel:shade:metal")
    if boarded:
        frame.pixel(round(x) + 10, round(y) + 8, "green")


def flame(frame, x, y, seconds, ground, throttle=1):
    pulse = 0.5 + 0.5 * math.sin(seconds * 29)
    length = max(2, round((4 + pulse * 3) * throttle))
    for row in range(min(length, max(0, ground - y))):
        half = max(0, round(2 * (1 - row / length)))
        for dx in range(-half, half + 1):
            color = "white" if dx == 0 and row < length // 2 else "gold" if abs(dx) < half else "flame"
            frame.pixel(x + dx, y + row, color)


def dust(frame, center, ground, seconds, strength):
    for i in range(round(32 * max(0, strength))):
        age = (seconds * 0.65 + i / 32) % 1
        side = -1 if i % 2 else 1
        x = center + round(side * (6 + age * (9 + i % 11)))
        y = ground - 1 - round(math.sin(age * math.pi) * (1 + i % 3) * strength)
        frame.pixel(x, y, "metal" if age < 0.35 else "shade")


def astronaut(frame, x, ground, seconds, jump=0, pose="walk"):
    x = round(x)
    y = round(ground * 2 - 12 - jump * 2)
    if pose == "kneel":
        y += 2
    body = ("   WWW   ", "  WcccW  ", "  WcccW  ", "   WWW   ",
            "  sWWWW  ", " sWWGWWs ", " sWWWWWs ", "  sWWWs  ")
    frame.sprite(x, y, body, _SPRITE_COLORS)
    # A small colored shoulder patch follows the suit, not the background.
    frame.pixel(x + 6, y + 5, "red")
    frame.pixel(x + 6, y + 6, "green")
    stride = round(math.sin(seconds * 9)) if pose == "walk" and not jump else 0
    for row in range(8, 10 if pose == "kneel" else 11):
        spread = round(stride * (row - 7) / 3)
        frame.pixel(x + 3 - spread, y + row, "white")
        frame.pixel(x + 5 + spread, y + row, "metal")
    if pose == "kneel":
        frame.pixel(x + 6, ground * 2 - 1, "white")
    else:
        frame.pixel(x + 2 - stride, y + 11, "white")
        frame.pixel(x + 6 + stride, y + 11, "white")
    if pose in {"plant", "salute"}:
        for dx, dy in [(7, 5), (8, 4), (8, 3), (7, 2)] if pose == "salute" else [(7, 5), (8, 5), (9, 5), (10, 5)]:
            frame.pixel(x + dx, y + dy, "white")
    else:
        for row in range(5, 8):
            frame.pixel(x + 1, y + row, "metal")
            frame.pixel(x + 7, y + row, "white")


def flag(frame, x, ground, raised=1, unfurled=1, planted=1):
    base = ground * 2
    pole_height = round(20 * max(0, min(1, planted)))
    top = base - pole_height
    for y in range(top, base):
        frame.pixel(x, y, "metal")
    if raised <= 0 or unfurled <= 0:
        return
    cloth_y = top + round((1 - raised) * max(0, pole_height - 8))
    visible = round(12 * min(1, unfurled))
    for y, row in enumerate(FLAG_PIXELS):
        for dx, color in enumerate(row[:visible]):
            frame.pixel(x + 1 + dx, cloth_y + y, {"r": "red", "w": "white", "g": "green"}[color])


def orbit(frame, seconds, progress):
    sky(frame, seconds)
    cx, cy = frame.width // 2, frame.height
    rx, ry = frame.width * 0.34, frame.height * 0.72
    angle = progress * 2 * math.pi
    ship_x = round(cx + rx * math.cos(angle)) - 4
    ship_y = round(cy + ry * math.sin(angle)) - 3
    orbiter = ("   ccc   ", "  sWWWs  ", " sWccWWs ", "  GGGGG  ", " sGgGGGs ", "ss     ss")
    if math.sin(angle) < 0:
        frame.sprite(ship_x, ship_y, orbiter, _SPRITE_COLORS)
    radius = min(frame.height - 3, frame.width // 5)
    for y in range(-radius, radius + 1):
        for x in range(-radius, radius + 1):
            if x * x + y * y <= radius * radius:
                color = "white" if x < -radius * .2 else "metal" if x < radius * .4 else "shade"
                for kx, ky, size in [(-.4, -.3, .23), (.1, .4, .19), (-.45, .45, .12), (.35, -.45, .14)]:
                    distance = math.hypot(x - kx * radius, y - ky * radius)
                    if distance < size * radius:
                        color = "shade" if x > kx * radius - 1 else "metal"
                frame.pixel(cx + x, cy + y, color)
    if math.sin(angle) >= 0:
        frame.sprite(ship_x, ship_y, orbiter, _SPRITE_COLORS)
    frame.text(1, frame.height - 1, "ARZI / LUNAR ORBIT", "cyan")
    return "Arzi glides past the Moon's sunlit craters."


def flight(frame, seconds, progress, phase):
    ground = frame.height - 2
    ground_px = ground * 2
    sky(frame, seconds, ground)
    earth(frame)
    final_y = ground_px - len(SHIP_PIXELS)
    x = (frame.width - 21) / 2
    burning = False
    if phase == "descent":
        x -= (1 - smooth(progress)) * frame.width * 0.22
        y = -6 + smooth(progress) * (final_y + 2)
        burning = True
        caption = "Braking burn. Arzi settles into a low hover." if progress < 1 else "HOVER HOLD. THE LANDING SITE IS CLEAR."
        strength = max(0, progress - 0.75) * 0.5
    elif phase == "landing":
        approach = min(1, progress / 0.68)
        y = final_y - 4 * (1 - smooth(approach))
        burning = progress < 0.76
        strength = max(0, min(1, (progress - 0.3) / 0.4)) * max(0, min(1, (1 - progress) / 0.24))
        caption = "Final approach. Ease Arzi onto the surface." if progress < 0.68 else "CONTACT. SHUTTING DOWN THE ENGINE." if burning else "ENGINE OFF. LET THE DUST SETTLE."
        if progress >= 1:
            caption = "CONTACT. THE ARZI HAS LANDED. TRANQUILITY IS QUIET."
    else:
        climb = max(0, (progress - 0.18) / 0.82) ** 1.55
        y = final_y - climb * (ground_px + len(SHIP_PIXELS))
        x += climb * 4
        burning = progress > 0.025
        strength = min(1, progress * 12) * max(0, 1 - climb * 3)
        caption = "Ignition. Build thrust, then climb into the stars." if progress < 1 else "ARZI / NEXT STOP: THE STARS."
    if burning:
        flame(frame, round(x) + 10, round(y) + 12, seconds, ground_px, 0.6 if phase == "landing" else 1)
    dust(frame, round(x) + 10, ground_px, seconds, strength)
    lander(frame, x, y)
    surface(frame, ground)
    frame.text(1, ground + 1, "SEA OF TRANQUILITY", "dim")
    return caption


def moonwalk(frame, seconds, progress):
    ground = frame.height - 2
    sky(frame, seconds, ground)
    earth(frame)
    ship_x = frame.width - 22
    flag_x = min(frame.width // 2 - 6, ship_x - 15)
    target = flag_x - 10
    surface(frame, ground)
    lander(frame, ship_x, ground * 2 - len(SHIP_PIXELS), boarded=progress >= 1)
    pose = "walk"
    if progress < 0.28:
        x = ship_x + (target - ship_x) * smooth(progress / 0.28)
        caption = "First footsteps. Carry Lebanon to Tranquility."
    elif progress < 0.38:
        x, pose = target, "kneel"
        flag(frame, flag_x, ground, unfurled=0, planted=(progress - .28) / .1)
        caption = "Set the pole firmly into the lunar soil."
    elif progress < 0.55:
        x, pose = target, "plant"
        flag(frame, flag_x, ground, unfurled=(progress - .38) / .17)
        caption = "Unfurl the Lebanese flag: red, white, and the green cedar."
    elif progress < 0.7:
        x, pose = target, "salute"
        flag(frame, flag_x, ground)
        caption = "THE LEBANESE FLAG, ON THE MOON."
    else:
        x = target + (ship_x - target) * smooth((progress - .7) / .3)
        flag(frame, flag_x, ground)
        caption = "A final salute, then home to Arzi."
    for step in range(target + 5, ship_x, 4):
        if progress >= .28 or step > x:
            frame.pixel(step, ground * 2 - 1, "shade")
    if progress < 1:
        astronaut(frame, x, ground, seconds, pose=pose)
    else:
        caption = "LEBANESE FLAG PLANTED. CREW SAFELY ABOARD ARZI."
    return caption


def moonhop(frame, seconds, progress):
    ground = frame.height - 2
    sky(frame, seconds, ground)
    surface(frame, ground)
    ship_x, flag_x = frame.width - 22, frame.width - 37
    lander(frame, ship_x, ground * 2 - len(SHIP_PIXELS), boarded=progress >= 1)
    centers = [round((flag_x - 6) * fraction) + 4 for fraction in (0.24, 0.5, 0.76)]
    runner = 1 + (flag_x - 10) * min(progress / 0.62, 1)
    stars, jump = 0, 0
    for i, center in enumerate(centers):
        crate_height = 2 + i % 2
        for row in range(crate_height * 2):
            for dx in range(-2, 2):
                frame.pixel(center + dx, ground * 2 - crate_height * 2 + row, "gold" if row == 0 or dx == -2 else "shade")
        star_y = ground - crate_height - 3
        if runner + 4 >= center:
            stars += 1
            since = runner + 4 - center
            if since < 2:
                frame.text(center - 2, max(0, star_y - 1), ". + .", "accent")
        else:
            frame.text(center, star_y, "*", "accent")
        distance = abs(runner + 4 - center)
        span = max(2, (centers[1] - centers[0]) * .48)
        jump = max(jump, max(0, 1 - (distance / span) ** 2) * 3.5)
    if progress < 0.62:
        x = runner
        caption = f"MOON HOP / STARS {stars} / 3"
        flag(frame, flag_x, ground, raised=0)
    elif progress < 0.85:
        x = flag_x - 9
        slide = (progress - .62) / .23
        jump = (1 - slide) * 3
        flag(frame, flag_x, ground, raised=slide)
        caption = "THREE STARS! RAISE THE LEBANESE FLAG."
    else:
        x = flag_x - 9 + (ship_x - flag_x + 9) * smooth((progress - .85) / .15)
        jump = 0
        flag(frame, flag_x, ground)
        caption = "ONE SMALL HOP. CREW ABOARD ARZI." if progress == 1 else "LEVEL CLEAR / BOARD ARZI"
    if progress < 1:
        astronaut(frame, x, ground, seconds, jump)
    return caption


def render_scene(index, seconds, width, height):
    scene = SCENES[index]
    frame = Canvas(width, height)
    progress = min(1, max(0, seconds / scene.duration))
    if scene.id == "orbit":
        caption = orbit(frame, seconds, progress)
    elif scene.id in {"descent", "landing", "liftoff"}:
        caption = flight(frame, seconds, progress, scene.id)
    elif scene.id == "moonwalk":
        caption = moonwalk(frame, seconds, progress)
    else:
        caption = moonhop(frame, seconds, progress)
    return frame, caption


class ScenePlayer:
    def __init__(self):
        self.index, self.elapsed, self.play_all = 0, 0.0, False

    @property
    def scene(self):
        return SCENES[self.index]

    @property
    def finished(self):
        return self.elapsed >= self.scene.duration and not (self.scene.loop and not self.play_all)

    def select(self, index, play_all=False):
        if not 0 <= index < len(SCENES):
            raise ValueError("Unknown scene")
        self.index, self.elapsed, self.play_all = index, 0.0, play_all

    def advance(self, seconds):
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError("Scene time must advance by a finite, nonnegative amount")
        self.elapsed += seconds
        if self.play_all:
            while self.elapsed >= self.scene.duration and self.index < len(SCENES) - 1:
                self.elapsed -= self.scene.duration
                self.index += 1
            self.elapsed = min(self.elapsed, self.scene.duration)
        elif self.scene.loop:
            self.elapsed %= self.scene.duration
        else:
            self.elapsed = min(self.elapsed, self.scene.duration)

    def seek(self, seconds):
        if not math.isfinite(seconds):
            raise ValueError("Seek must be finite")
        self.elapsed = min(self.scene.duration, max(0, self.elapsed + seconds))
