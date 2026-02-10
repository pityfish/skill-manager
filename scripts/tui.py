#!/usr/bin/env python3
import sys
import tty
import termios


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

        while True:
            # Prepare buffer
            buffer = []

            # Title
            buffer.append(f"\033[1;36m◆  {self.title}\033[0m")
            buffer.append("")

            # Calculate visible range
            start = self.scroll_offset
            end = min(start + self.max_height, len(self.options))

            # Determine which sections are relevant to display
            # We need to insert section headers into the view
            # This is tricky with scrolling.
            # Simplified approach: Render ALL, then slice? No, inefficient.
            # Iterate options and inject headers.

            lines_to_print = []

            for i, opt in enumerate(self.options):
                # Check for section header
                for sec in self.sections:
                    if sec["start_index"] == i:
                        lines_to_print.append("")
                        lines_to_print.append(
                            f"\033[1m  ── {sec['title']} ──────────────────────────────\033[0m"
                        )

                # Render item
                is_selected = i == self.cursor_idx
                is_disabled = opt.get("disabled", False)

                marker = "❯" if is_selected else " "

                if is_disabled:
                    checkbox = "✓" if opt["checked"] else " "  # Fixed item
                    # Use a dimmer color for disabled items? Or Green for checked?
                    # Let's keep it simple: Green ✓
                    if opt["checked"]:
                        checkbox = "\033[32m✓\033[0m"  # Green check
                else:
                    checkbox = "●" if opt["checked"] else "○"

                color = "\033[36m" if is_selected else ""  # Cyan for selection
                reset = "\033[0m"

                label = opt["label"]
                if is_selected:
                    line = f"{color} {marker} {checkbox} {label}{reset}"
                else:
                    line = f"   {checkbox} {label}"

                lines_to_print.append(line)

            # Viewport Slicing (basic)
            # If we have sections, the line count > option count.
            # Let's just print all for now (unless list is huge). user has ~30 items.
            # If > 20 lines, we might need scrolling but `install_skill.py` usually isn't THAT huge.
            # Let's try printing all first.

            # Clear previous output
            if not first_draw:
                # Move up N lines
                sys.stdout.write(f"\033[{len(prev_lines)}A")  # Move up
                sys.stdout.write("\033[J")  # Clear below

            print("\n".join(buffer + lines_to_print))
            prev_lines = buffer + lines_to_print
            first_draw = False

            # Input
            key = self.get_key()

            if key == "\x1b[A":  # Up
                self.cursor_idx = max(0, self.cursor_idx - 1)
            elif key == "\x1b[B":  # Down
                self.cursor_idx = min(len(self.options) - 1, self.cursor_idx + 1)
            elif key == " ":  # Space
                # Only toggle if not disabled
                if not self.options[self.cursor_idx].get("disabled"):
                    if self.single_select:
                        # Uncheck all and check current
                        for opt in self.options:
                            opt["checked"] = False
                        self.options[self.cursor_idx]["checked"] = True
                    else:
                        self.options[self.cursor_idx]["checked"] = not self.options[
                            self.cursor_idx
                        ]["checked"]

            elif key == "\r":  # Enter
                # In single select, implicitly select the one under cursor before breaking?
                # Or just use the current selection.
                # Usually Enter = Confirm.
                if self.single_select:
                    # Ensure current is checked if nothing is checked?
                    # Let's say if single_select, Enter confirms the current cursor pos.
                    for opt in self.options:
                        opt["checked"] = False
                    self.options[self.cursor_idx]["checked"] = True
                break
            elif key == "\x03":  # Ctrl+C
                sys.exit(1)

        # Final cleanup: clear and print result summary?
        # Or just leave it.
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
