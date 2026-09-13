import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame")

import sys
import ctypes
from pathlib import Path

import pygame


def resource_path(name):
    """兼容 PyInstaller 打包后的资源路径。"""
    base = getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)
    return str(Path(base) / name)


class Player:
    def __init__(self, screensaver_mode=True):
        self.screensaver_mode = screensaver_mode

        pygame.init()
        self.clock = pygame.time.Clock()

        if screensaver_mode:
            self.screen = pygame.display.set_mode(
                (0, 0), pygame.FULLSCREEN
            )
        else:
            self.screen = pygame.display.set_mode((800, 600))

        pygame.display.set_caption("screensaver")
        pygame.mouse.set_visible(not screensaver_mode)

        self.screen_rect = self.screen.get_rect()
        self.bg_color = (0, 0, 0)

        self.original_image = pygame.image.load(
            resource_path("plantcell-black20.png")
        ).convert_alpha()
        self.image = self.original_image.copy()

        # 图片过大时等比例缩小，确保能在窗口内运动。
        width, height = self.original_image.get_size()
        scale = min(
            1.0,
            self.screen_rect.width / width,
            self.screen_rect.height / height,
        )
        if scale < 1.0:
            self.original_image = pygame.transform.scale(
                self.original_image,
                (
                    max(1, int(width * scale)),
                    max(1, int(height * scale)),
                ),
            )

        self.rect = self.image.get_rect(topleft=(100, 300))
        self.rect.clamp_ip(self.screen_rect)

        # Rect 使用整数，另存浮点位置避免小数速度丢失。
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)

        self.speed = 90.0  # 像素/秒，相当于 60 FPS 时每帧 1.5 像素
        self.direction_x = 1
        self.direction_y = -1
        self.flip_x = False
        self.flip_y = False

        self.start_ticks = pygame.time.get_ticks()
        self.ignore_mouse_ms = 1000

    def run_game(self):
        try:
            while True:
                dt = min(self.clock.tick(60) / 1000.0, 0.05)

                if not self._check_events():
                    break

                self._move(dt)
                self._update_screen()
        finally:
            pygame.quit()

    def _check_events(self):
        for ev in pygame.event.get():
            if ev.type in (pygame.QUIT, pygame.KEYDOWN):
                return False

            if (
                self.screensaver_mode
                and ev.type in (
                    pygame.MOUSEMOTION,
                    pygame.MOUSEBUTTONDOWN,
                )
            ):
                elapsed = pygame.time.get_ticks() - self.start_ticks
                if elapsed > self.ignore_mouse_ms:
                    return False

        return True

    def _update_screen(self):
        self.screen.fill(self.bg_color)
        self.screen.blit(self.image, self.rect)
        pygame.display.flip()

    def _move(self, dt):
        self.x += self.speed * self.direction_x * dt
        self.y += self.speed * self.direction_y * dt

        max_x = self.screen_rect.width - self.rect.width
        max_y = self.screen_rect.height - self.rect.height

        flip_x = False
        flip_y = False

        if max_x <= 0:
            self.x = 0.0
        elif self.direction_x > 0 and self.x >= max_x:
            self.x = float(max_x)
            self.direction_x = -1
            flip_x = True
        elif self.direction_x < 0 and self.x <= 0:
            self.x = 0.0
            self.direction_x = 1
            flip_x = True

        if max_y <= 0:
            self.y = 0.0
        elif self.direction_y > 0 and self.y >= max_y:
            self.y = float(max_y)
            self.direction_y = -1
            flip_y = True
        elif self.direction_y < 0 and self.y <= 0:
            self.y = 0.0
            self.direction_y = 1
            flip_y = True

        if flip_x:
            self.flip_x = not self.flip_x
        if flip_y:
            self.flip_y = not self.flip_y

        if flip_x or flip_y:
            self.image = pygame.transform.flip(
                self.original_image,
                self.flip_x,
                self.flip_y,
            )

        self.rect.topleft = (round(self.x), round(self.y))


def main():
    args = sys.argv[1:]
    first = args[0].lower() if args else "/s"

    if first.startswith("/c"):
        if sys.platform == "win32":
            ctypes.windll.user32.MessageBoxW(
                0, "此屏保无需配置", "提示", 0
            )
        else:
            print("此屏保无需配置")
    elif first.startswith("/p"):
        # 普通窗口预览；尚未实现嵌入 Windows 屏保预览框。
        Player(screensaver_mode=False).run_game()
    else:
        Player(screensaver_mode=True).run_game()


if __name__ == "__main__":
    try:
        main()
    except (pygame.error, OSError) as exc:
        pygame.quit()
        message = (
            f"启动失败：{exc}\n\n"
            "请确认 plantcell-black20.png 位于程序同一目录，"
            "或已作为资源打包。"
        )
        if sys.platform == "win32":
            ctypes.windll.user32.MessageBoxW(
                0, message, "屏保错误", 0x10
            )
        else:
            print(message, file=sys.stderr)
        sys.exit(1)
