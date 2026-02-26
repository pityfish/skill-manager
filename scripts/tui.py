#!/usr/bin/env python3
import sys
import tty
import termios
import shutil
import re

ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


class MultiSelectMenu:
    def __init__(self, title, options, sections=None, single_select=False):
        """
        options: List of dicts {'id': str, 'label': str, 'checked': bool}
        sections: List of dicts {'title': str, 'start_index': int} (optional dividers)
        single_select: If True, only one item can be checked at a time
        """
        self.title = title
        self.options = options
        self.sections = sections or []
        self.single_select = single_select
        self.cursor_idx = 0
        self.scroll_offset = 0
        self.max_height = 15  # Max visible items

    def get_key(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                ch += sys.stdin.read(2)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def render(self):
        # Clear screen (or move cursor up)
        # Assuming we just redraw from current position?
        # Better: We print newline first time, then move up N lines
        pass

    def run(self):
        # Initial draw
        first_draw = True
        prev_lines = []

        while True:
            # Get terminal size
            try:
                cols, rows = shutil.get_terminal_size(fallback=(80, 24))
            except Exception:
                cols, rows = 80, 24

            # Dynamic max height based on screen size to prevent overflow
            # Title (2) + Footer (2) + prompt (about 4) = approx 8
            self.max_height = max(5, min(15, rows - 8))

            # Safety margin
            width = max(20, cols - 1)

            # 1. Build Content Buffer (Options + Sections)
            content_lines = []
            option_line_map = {}  # map option index -> line index in content_lines

            for i, opt in enumerate(self.options):
                # Add section header if needed
                for sec in self.sections:
                    if sec["start_index"] == i:
                        content_lines.append("")
                        # Truncate title line if needed (simple approximation)
                        raw_title = (
                            f"  ── {sec['title']} ──────────────────────────────"
                        )
                        if len(raw_title) > width:
                            raw_title = raw_title[:width]

                        content_lines.append(f"\033[1m{raw_title}\033[0m")

                # Track where this option is printed
                line_idx = len(content_lines)
                option_line_map[i] = line_idx

                # Render item
                is_selected = i == self.cursor_idx
                is_disabled = opt.get("disabled", False)

                marker = "❯" if is_selected else " "

                if is_disabled:
                    checkbox = "✓" if opt["checked"] else " "
                    if opt["checked"]:
                        checkbox = "\033[32m✓\033[0m"  # Green check
                else:
                    checkbox = "●" if opt["checked"] else "○"

                color = "\033[36m" if is_selected else ""  # Cyan
                reset = "\033[0m"

                label = opt["label"]

                # Truncate label to fit screen
                # Prefix takes about 7 chars: "   ○ " or " ❯ ● "
                prefix_len = 7
                avail_label = max(5, width - prefix_len - 2)  # -2 safety

                real_len = len(ANSI_ESCAPE.sub("", label))
                if real_len > avail_label:
                    label = label[: avail_label + 10] + "...\033[0m"

                if is_selected:
                    line = f"{color} {marker} {checkbox} {label}{reset}"
                else:
                    line = f"   {checkbox} {label}"

                content_lines.append(line)

            # 2. Update Scroll Offset to keep cursor visible
            if self.options:
                cursor_line = option_line_map[self.cursor_idx]

                # If cursor is above viewport
                if cursor_line < self.scroll_offset:
                    self.scroll_offset = cursor_line

                # If cursor is below viewport
                # logical height of viewport is max_height
                # visible range is [scroll_offset, scroll_offset + max_height)
                elif cursor_line >= self.scroll_offset + self.max_height:
                    self.scroll_offset = cursor_line - self.max_height + 1

                # Clamp offset
                max_scroll = max(0, len(content_lines) - self.max_height)
                self.scroll_offset = min(self.scroll_offset, max_scroll)
            else:
                self.scroll_offset = 0

            # 3. Slice Visible Area
            visible_lines = content_lines[
                self.scroll_offset : self.scroll_offset + self.max_height
            ]

            # 4. Prepare Final Output Buffer
            buffer = []
            # Title
            buffer.append(f"\033[1;36m◆  {self.title}\033[0m")
            buffer.append("")

            # Visible Lines
            buffer.extend(visible_lines)

            # Footer
            if self.single_select:
                footer = "\033[2m  ↑↓ move, enter confirm\033[0m"
            else:
                footer = "\033[2m  ↑↓ move, space select, enter confirm\033[0m"

            buffer.append("")
            buffer.append(footer)

            # Reserve space efficiently on first draw to avoid being pushed off-screen.
            if first_draw:
                sys.stdout.write("\n" * len(buffer))
                sys.stdout.flush()
                sys.stdout.write(f"\033[{len(buffer)}A")
                sys.stdout.flush()

            # Clear previous output
            if not first_draw:
                # Move up N lines
                if prev_lines:
                    sys.stdout.write(f"\033[{len(prev_lines)}A")  # Move up
                    sys.stdout.write("\033[J")  # Clear below

            # Print
            print("\n".join(buffer))
            prev_lines = buffer
            first_draw = False

            # Input
            key = self.get_key()

            if key == "\x1b[A":  # Up
                self.cursor_idx = max(0, self.cursor_idx - 1)
            elif key == "\x1b[B":  # Down
                self.cursor_idx = min(len(self.options) - 1, self.cursor_idx + 1)
            elif key == " ":  # Space
                # Only toggle if not disabled
                if self.options and not self.options[self.cursor_idx].get("disabled"):
                    if self.single_select:
                        for opt in self.options:
                            opt["checked"] = False
                        self.options[self.cursor_idx]["checked"] = True
                    else:
                        self.options[self.cursor_idx]["checked"] = not self.options[
                            self.cursor_idx
                        ]["checked"]

            elif key == "\r":  # Enter
                if self.single_select and self.options:
                    for opt in self.options:
                        opt["checked"] = False
                    self.options[self.cursor_idx]["checked"] = True
                break
            elif key == "\x03":  # Ctrl+C
                sys.exit(1)

        # Return result
        checked_ids = [opt["id"] for opt in self.options if opt["checked"]]
        if self.single_select:
            return checked_ids[0] if checked_ids else None
        return checked_ids


if __name__ == "__main__":
    # Test
    opts = [
        {"id": "1", "label": "Option 1", "checked": True},
        {"id": "2", "label": "Option 2", "checked": False},
    ]
    menu = MultiSelectMenu("Test Menu", opts)
    print(menu.run())
