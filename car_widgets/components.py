"""Reusable Tkinter components for the provisional car widget UI."""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont

from . import theme
from .scenarios import get_condition_guidance


class Fonts:
    def __init__(self) -> None:
        self.title = tkfont.Font(family=theme.FONT_FAMILY, size=22, weight="bold")
        self.h1 = tkfont.Font(family=theme.FONT_FAMILY, size=18, weight="bold")
        self.h2 = tkfont.Font(family=theme.FONT_FAMILY, size=14, weight="bold")
        self.body = tkfont.Font(family=theme.FONT_FAMILY, size=11)
        self.small = tkfont.Font(family=theme.FONT_FAMILY, size=10)
        self.mono = tkfont.Font(family=theme.FONT_MONO, size=10)


def card(parent: tk.Misc, *, padx: int = 16, pady: int = 14) -> tk.Frame:
    frame = tk.Frame(parent, bg=theme.SURFACE, padx=padx, pady=pady)
    frame.config(highlightbackground=theme.BORDER, highlightthickness=1)
    return frame


def title(parent: tk.Misc, text: str, fonts: Fonts, subtitle: str = "") -> tk.Frame:
    frame = tk.Frame(parent, bg=parent.cget("bg"))
    frame.pack(fill="x", anchor="w")
    tk.Label(frame, text=text, font=fonts.h2, bg=frame.cget("bg"), fg=theme.TEXT).pack(anchor="w")
    if subtitle:
        tk.Label(frame, text=subtitle, font=fonts.small, bg=frame.cget("bg"), fg=theme.TEXT_DIM).pack(anchor="w")
    return frame


def button(parent: tk.Misc, text: str, command, *, primary: bool = False, danger: bool = False) -> tk.Button:
    bg = theme.ACCENT_DARK if primary else theme.SURFACE_ALT
    fg = theme.BG if primary else theme.TEXT
    active_bg = theme.ACCENT if primary else theme.SURFACE_ACTIVE
    if danger:
        bg = "#3a2229"
        fg = theme.TEXT
        active_bg = theme.DANGER
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg=fg,
        activebackground=active_bg,
        activeforeground=fg,
        relief="flat",
        bd=0,
        padx=12,
        pady=8,
        cursor="hand2",
    )


def clear(frame: tk.Misc) -> None:
    for child in frame.winfo_children():
        child.destroy()


def render_guidance(parent: tk.Misc, condition: str, fonts: Fonts) -> None:
    clear(parent)
    guidance = get_condition_guidance(condition)
    tk.Label(
        parent,
        text=guidance["title"],
        font=fonts.h2,
        bg=theme.SURFACE,
        fg=theme.TEXT,
    ).pack(anchor="w")
    tk.Label(
        parent,
        text=guidance["description"],
        font=fonts.body,
        bg=theme.SURFACE,
        fg=theme.TEXT_MUTED,
        wraplength=420,
        justify="left",
    ).pack(anchor="w", pady=(6, 10))

    voice_examples = guidance.get("voice_examples", ())
    if voice_examples:
        tk.Label(parent, text="Beispiele", font=fonts.small, bg=theme.SURFACE, fg=theme.TEXT_DIM).pack(anchor="w")
        tk.Label(
            parent,
            text="  ".join(f"'{example}'" for example in voice_examples),
            font=fonts.body,
            bg=theme.SURFACE,
            fg=theme.TEXT,
            wraplength=420,
            justify="left",
        ).pack(anchor="w", pady=(2, 8))

    gestures = guidance.get("gestures", ())
    if gestures:
        tk.Label(parent, text="Gesten", font=fonts.small, bg=theme.SURFACE, fg=theme.TEXT_DIM).pack(anchor="w")
        for name, description in gestures:
            tk.Label(
                parent,
                text=f"{name}: {description}",
                font=fonts.body,
                bg=theme.SURFACE,
                fg=theme.TEXT,
                anchor="w",
            ).pack(fill="x", pady=1)


def render_feedback(parent: tk.Misc, decision: str, text: str, fonts: Fonts) -> None:
    clear(parent)
    normalized = {
        "accepted": "execute",
        "rejected": "cancel",
        "unclear": "clarify",
    }.get(decision, decision)
    color = {
        "execute": theme.SUCCESS,
        "cancel": theme.DANGER,
        "clarify": theme.WARNING,
    }.get(normalized, theme.TEXT_MUTED)
    label = {
        "execute": "Ausfuehren",
        "cancel": "Abbrechen / ablehnen",
        "clarify": "Rueckfrage",
    }.get(normalized, "Status")
    tk.Label(parent, text=label, font=fonts.h2, bg=theme.SURFACE, fg=color).pack(anchor="w")
    tk.Label(parent, text=text, font=fonts.body, bg=theme.SURFACE, fg=theme.TEXT_MUTED,
             wraplength=420, justify="left").pack(anchor="w", pady=(4, 0))


def render_overlay(parent: tk.Misc, title_text: str, body: str, clarification: str, fonts: Fonts) -> None:
    clear(parent)
    tk.Label(parent, text=title_text, font=fonts.h1, bg=theme.SURFACE_ALT, fg=theme.TEXT).pack(anchor="w")
    tk.Label(parent, text=body, font=fonts.body, bg=theme.SURFACE_ALT, fg=theme.TEXT_MUTED,
             wraplength=500, justify="left").pack(anchor="w", pady=(8, 0))
    if clarification:
        tk.Label(parent, text=clarification, font=fonts.h2, bg=theme.SURFACE_ALT,
                 fg=theme.WARNING, wraplength=500, justify="left").pack(anchor="w", pady=(12, 0))
