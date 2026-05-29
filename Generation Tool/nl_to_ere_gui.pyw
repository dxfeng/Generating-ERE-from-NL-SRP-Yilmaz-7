from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox


SECTION_MARKER = "@$#%"
SCRIPT_DIR = Path(__file__).resolve().parent
INITIATE_PATH = SCRIPT_DIR / "initiate.py"
TRANSLATION_PATH = SCRIPT_DIR / "translation.txt"


def parse_translation_file(file_path: Path) -> list[str]:
    raw_text = file_path.read_text(encoding="utf-8", errors="replace")
    sections = [
        section.strip()
        for section in raw_text.split(SECTION_MARKER)
        if section.strip()
    ]

    if len(sections) != 5:
        raise ValueError(
            f"Expected 5 sections in {file_path.name}, but found {len(sections)}."
        )

    return sections


class ReadOnlyText(tk.Text):
    def __init__(self, master: tk.Misc, *, height: int) -> None:
        super().__init__(
            master,
            height=height,
            wrap="word",
            font=("Segoe UI", 11),
            bg="white",
            fg="black",
            relief="solid",
            borderwidth=2,
            padx=8,
            pady=8,
        )
        self.configure(state="disabled")

    def set_text(self, value: str) -> None:
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.insert("1.0", value)
        self.configure(state="disabled")


class TranslationApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("NL To ERE GUI")
        self.root.geometry("680x620")
        self.root.minsize(680, 620)
        self.root.configure(bg="white")

        container = tk.Frame(
            root,
            bg="white",
            highlightbackground="black",
            highlightthickness=3,
            bd=0,
            padx=22,
            pady=22,
        )
        container.pack(fill="both", expand=True, padx=14, pady=14)
        container.grid_columnconfigure(0, weight=1)

        input_row = tk.Frame(container, bg="white")
        input_row.grid(row=0, column=0, sticky="ew")
        input_row.grid_columnconfigure(1, weight=1)

        tk.Label(
            input_row,
            text="INPUT:",
            font=("Segoe UI", 15),
            bg="white",
            fg="black",
        ).grid(row=0, column=0, sticky="w", padx=(0, 14))

        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(
            input_row,
            textvariable=self.input_var,
            font=("Segoe UI", 11),
            bg="white",
            fg="black",
            relief="solid",
            borderwidth=2,
        )
        self.input_entry.grid(row=0, column=1, sticky="ew", ipady=6, padx=(0, 14))

        self.gen_button = tk.Button(
            input_row,
            text="GEN",
            font=("Segoe UI", 17),
            bg="white",
            fg="black",
            relief="solid",
            borderwidth=2,
            padx=16,
            pady=16,
            command=self.generate_translation,
        )
        self.gen_button.grid(row=0, column=2, sticky="ns")

        self._add_separator(container, row=1)

        self.nl_box = self._create_section(container, row=2, label="NL:", height=5)
        self.params_box = self._create_section(
            container, row=3, label="PARAMS:", height=2
        )
        self.events_box = self._create_section(
            container, row=4, label="EVENTS:", height=5
        )
        self.handler_box = self._create_section(
            container, row=5, label="HANDLER:", height=2
        )

        self._add_separator(container, row=6)

        self.output_box = self._create_section(
            container, row=7, label="ERE OUTPUT", height=2
        )

        self.input_entry.focus_set()

    def _add_separator(self, master: tk.Frame, *, row: int) -> None:
        separator = tk.Canvas(master, height=10, bg="white", highlightthickness=0)
        separator.grid(row=row, column=0, sticky="ew", pady=(12, 12))
        separator.bind(
            "<Configure>",
            lambda event: (
                separator.delete("all"),
                separator.create_line(
                    0, 5, event.width, 5, fill="black", dash=(2, 2)
                ),
            ),
        )

    def _create_section(
        self, master: tk.Frame, *, row: int, label: str, height: int
    ) -> ReadOnlyText:
        frame = tk.Frame(master, bg="white")
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 16))
        frame.grid_columnconfigure(0, weight=1)

        tk.Label(
            frame,
            text=label,
            font=("Segoe UI", 15),
            bg="white",
            fg="black",
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        text_box = ReadOnlyText(frame, height=height)
        text_box.grid(row=1, column=0, sticky="ew")
        return text_box

    def generate_translation(self) -> None:
        input_path = Path(self.input_var.get().strip().strip('"'))

        if not input_path:
            messagebox.showerror("Missing Input", "Enter the path to a .txt file.")
            return

        if input_path.suffix.lower() != ".txt":
            messagebox.showerror("Invalid Input", "The input file must be a .txt file.")
            return

        if not input_path.exists():
            messagebox.showerror("File Not Found", f"Could not find:\n{input_path}")
            return

        self.gen_button.configure(state="disabled")
        self.root.update_idletasks()

        try:
            subprocess.run(
                [sys.executable, str(INITIATE_PATH), str(input_path)],
                cwd=SCRIPT_DIR,
                check=True,
                capture_output=True,
                text=True,
            )

            nl_text, params_text, events_text, handler_text, output_text = (
                parse_translation_file(TRANSLATION_PATH)
            )

            self.nl_box.set_text(nl_text)
            self.params_box.set_text(params_text)
            self.events_box.set_text(events_text)
            self.handler_box.set_text(handler_text)
            self.output_box.set_text(output_text)
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.strip() or exc.stdout.strip() or str(exc)
            messagebox.showerror(
                "Generation Failed",
                f"`initiate.py` did not complete successfully.\n\n{stderr}",
            )
        except FileNotFoundError:
            messagebox.showerror(
                "Missing File",
                "The app expected `translation.txt` to be created, but it was not found.",
            )
        except ValueError as exc:
            messagebox.showerror("Invalid Translation Format", str(exc))
        except Exception as exc:
            messagebox.showerror("Unexpected Error", str(exc))
        finally:
            self.gen_button.configure(state="normal")


def main() -> None:
    root = tk.Tk()
    TranslationApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
