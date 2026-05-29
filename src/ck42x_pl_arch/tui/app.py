from __future__ import annotations

import asyncio
from pathlib import Path

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Footer, Input, Label, RichLog, Static, TextArea

from ck42x_pl_arch import __version__
from ck42x_pl_arch.config import Settings
from ck42x_pl_arch.forge.mission import ForgeRequest, forge_mission

_BOX_INNER = 62


def _banner_line(text: str) -> str:
    return f"| {text[:_BOX_INNER].ljust(_BOX_INNER)} |"


BANNER = "\n".join(
    [
        "+" + "=" * (_BOX_INNER + 2) + "+",
        _banner_line(r"     \     /"),
        _banner_line(r"      \   /    CK42X  ::  PAYLOAD LAB ARCHITECT"),
        _banner_line(r"       ) (     PL-ARCH  //  BEE OPS"),
        _banner_line(r"      / . \    BLACK + GOLD  |  Authorized labs only"),
        _banner_line(r"     /     \"),
        "+" + "=" * (_BOX_INNER + 2) + "+",
    ]
)


class MainMenuScreen(Screen):
    BINDINGS = [
        Binding("up,k", "cursor_up", "Up", show=False),
        Binding("down,j", "cursor_down", "Down", show=False),
        Binding("enter", "select_item", "Select", show=False),
        Binding("1", "pick(0)", show=False),
        Binding("2", "pick(1)", show=False),
        Binding("3", "pick(2)", show=False),
        Binding("4", "pick(3)", show=False),
        Binding("5", "pick(4)", show=False),
        Binding("q", "quit", "Quit"),
    ]

    MENU = [
        ("forge", ">  Forge Mission Payload", "Build .txt + host scripts for Flipper labs"),
        ("library", ">  Mission Library", "Open output folder & recent bundles"),
        ("settings", ">  Settings", "DeepSeek API key - output path - model"),
        ("install", ">  Install Command", "One-liner for teammates / ck42x.com"),
        ("quit", ">  Quit", "Exit PL-ARCH"),
    ]

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings
        self.index = 0

    def compose(self) -> ComposeResult:
        yield Static(BANNER, id="main-header")
        items = []
        for i, (_key, label, hint) in enumerate(self.MENU):
            items.append(Static(f"{label}\n[dim]{hint}[/dim]", classes="menu-item", id=f"item-{i}"))
        yield Vertical(*items, id="menu-panel")
        yield Static("", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        self._sync_highlight()
        out = self.settings.output_path
        key = "configured" if self.settings.deepseek_api_key else "not set"
        self.query_one("#status-bar", Static).update(
            f" v{__version__} | output: {out} | deepseek: {key} | up/down navigate, enter select, q quit "
        )

    def _sync_highlight(self) -> None:
        for i in range(len(self.MENU)):
            w = self.query_one(f"#item-{i}", Static)
            w.remove_class("-active")
            if i == self.index:
                w.add_class("-active")

    def action_cursor_up(self) -> None:
        self.index = (self.index - 1) % len(self.MENU)
        self._sync_highlight()

    def action_cursor_down(self) -> None:
        self.index = (self.index + 1) % len(self.MENU)
        self._sync_highlight()

    def action_pick(self, n: int) -> None:
        self.index = n
        self.action_select_item()

    def action_select_item(self) -> None:
        key = self.MENU[self.index][0]
        if key == "forge":
            self.app.push_screen(ForgeScreen(self.settings))
        elif key == "library":
            self.app.push_screen(LibraryScreen(self.settings))
        elif key == "settings":
            self.app.push_screen(SettingsScreen(self.settings))
        elif key == "install":
            self.app.push_screen(InstallScreen())
        elif key == "quit":
            self.app.exit()


class ForgeScreen(Screen):
    BINDINGS = [Binding("escape", "pop_screen", "Back")]

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings

    def compose(self) -> ComposeResult:
        yield Static("[bold #ffd400]Forge Mission Payload[/]", id="main-header")
        yield Label("Mission title")
        yield Input(placeholder="e.g. repo-health-check", id="title")
        yield Label("Mission goal (what should the host agent accomplish?)")
        yield TextArea(id="goal")
        yield Label("Platforms")
        with Horizontal():
            yield Checkbox("Windows (.txt + .ps1)", value=True, id="win")
            yield Checkbox("Linux (.sh)", value=True, id="linux")
            yield Checkbox("macOS (.sh)", value=True, id="mac")
        yield Checkbox("Mass Storage handoff (PAYLOADBAY scripts/)", value=True, id="handoff")
        yield Checkbox(
            "Deploy to Flipper after forge (launch .txt + PAYLOADBAY scripts/)",
            value=self.settings.auto_deploy_after_forge,
            id="deploy",
        )
        with Horizontal():
            yield Button("Generate bundle", variant="primary", id="go")
            yield Button("Back", id="back")
        yield RichLog(id="log", highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#goal", TextArea).text = (
            "Inspect the lab workstation and propose safe read-only verification commands."
        )

    @on(Button.Pressed, "#back")
    def back(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#go")
    def generate(self) -> None:
        self.run_forge()

    @work(exclusive=True)
    async def run_forge(self) -> None:
        log = self.query_one("#log", RichLog)
        log.clear()
        title = self.query_one("#title", Input).value.strip()
        goal = self.query_one("#goal", TextArea).text.strip()
        if not title or not goal:
            log.write("[red]Title and goal are required.[/]")
            return

        platforms: list[str] = []
        if self.query_one("#win", Checkbox).value:
            platforms.append("windows")
        if self.query_one("#linux", Checkbox).value:
            platforms.append("linux")
        if self.query_one("#mac", Checkbox).value:
            platforms.append("macos")
        if not platforms:
            log.write("[red]Select at least one platform.[/]")
            return

        handoff = self.query_one("#handoff", Checkbox).value
        deploy = self.query_one("#deploy", Checkbox).value
        log.write("[#ffd400]Forging mission bundle...[/]")

        try:
            result = await forge_mission(
                self.settings,
                ForgeRequest(
                    title=title,
                    goal=goal,
                    platforms=platforms,
                    handoff=handoff,
                    deploy=deploy,
                ),
            )
        except Exception as exc:  # noqa: BLE001
            log.write(f"[red]Forge failed:[/] {exc}")
            return

        log.write(f"[green]Done.[/] slug=[bold]{result.slug}[/]")
        log.write(f"[dim]risk={result.risk}[/]")
        for note in result.notes:
            log.write(f"[yellow]*[/] {note}")
        log.write("[bold]Files:[/]")
        for name in result.files:
            log.write(f"  - {name}")
        log.write(f"\n[#ffd400]Bundle:[/] {result.bundle_dir}")
        if result.deploy_logs:
            log.write("[bold]Flipper deploy:[/]")
            for line in result.deploy_logs:
                color = "green" if line.startswith("[ok]") else "red" if line.startswith("[error]") else "dim"
                log.write(f"[{color}]{line}[/]")
        elif not deploy:
            log.write("[dim]Enable 'Deploy to Flipper' or run: ck42x deploy[/]")


class SettingsScreen(Screen):
    BINDINGS = [Binding("escape", "pop_screen", "Back")]

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings

    def compose(self) -> ComposeResult:
        yield Static("[bold #ffd400]Settings[/]", id="main-header")
        yield Label("DeepSeek API key (stored locally)")
        yield Input(password=True, id="key")
        yield Label("Model")
        yield Input(id="model")
        yield Label("Output directory")
        yield Input(id="out")
        yield Label("Flipper serial port (optional, e.g. COM10)")
        yield Input(placeholder="auto-detect", id="flipper_port")
        yield Checkbox("Deploy to Flipper after forge by default", id="auto_deploy")
        with Horizontal():
            yield Button("Save", variant="primary", id="save")
            yield Button("Back", id="back")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#key", Input).value = self.settings.deepseek_api_key
        self.query_one("#model", Input).value = self.settings.deepseek_model
        self.query_one("#out", Input).value = self.settings.output_dir
        self.query_one("#flipper_port", Input).value = self.settings.flipper_port
        self.query_one("#auto_deploy", Checkbox).value = self.settings.auto_deploy_after_forge

    @on(Button.Pressed, "#back")
    def back(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#save")
    def save(self) -> None:
        self.settings.deepseek_api_key = self.query_one("#key", Input).value.strip()
        self.settings.deepseek_model = self.query_one("#model", Input).value.strip() or "deepseek-chat"
        self.settings.output_dir = self.query_one("#out", Input).value.strip() or str(self.settings.output_path)
        self.settings.flipper_port = self.query_one("#flipper_port", Input).value.strip()
        self.settings.auto_deploy_after_forge = self.query_one("#auto_deploy", Checkbox).value
        self.settings.save()
        self.app.pop_screen()


class LibraryScreen(Screen):
    BINDINGS = [Binding("escape", "pop_screen", "Back")]

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings

    def compose(self) -> ComposeResult:
        yield Static("[bold #ffd400]Mission Library[/]", id="main-header")
        yield RichLog(id="log", highlight=True, markup=True)
        yield Button("Back", id="back")
        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        root = self.settings.output_path
        root.mkdir(parents=True, exist_ok=True)
        log.write(f"[#ffd400]Output root:[/] {root}\n")
        missions = sorted([p for p in root.iterdir() if p.is_dir()])
        if not missions:
            log.write("[dim]No missions yet. Use Forge Mission Payload.[/]")
            return
        for m in missions:
            manifest = m / "manifest.json"
            tag = "[green][ok][/]" if manifest.exists() else "[yellow]?[/]"
            log.write(f"{tag} [bold]{m.name}[/]")
            for f in sorted(m.glob("*")):
                if f.is_file():
                    log.write(f"    [dim]{f.name}[/] ({f.stat().st_size} B)")

    @on(Button.Pressed, "#back")
    def back(self) -> None:
        self.app.pop_screen()


class InstallScreen(Screen):
    BINDINGS = [Binding("escape", "pop_screen", "Back")]

    INSTALL_SH = "curl -fsSL https://www.ck42x.com/install/ck42x-pl-arch.sh | bash"
    INSTALL_PS = "irm https://www.ck42x.com/install/ck42x-pl-arch.ps1 | iex"

    def compose(self) -> ComposeResult:
        yield Static("[bold #ffd400]Install Command[/]", id="main-header")
        yield RichLog(id="log", highlight=True, markup=True)
        yield Button("Back", id="back")
        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write("[bold]Linux / macOS[/]")
        log.write(f"[#ffea00]{self.INSTALL_SH}[/]\n")
        log.write("[bold]Windows (PowerShell)[/]")
        log.write(f"[#ffea00]{self.INSTALL_PS}[/]\n")
        log.write("[dim]Paste on ck42x.com Payload Bay page for operators.[/]")

    @on(Button.Pressed, "#back")
    def back(self) -> None:
        self.app.pop_screen()


class PlArchApp(App):
    TITLE = "CK42X PL-ARCH"
    SUB_TITLE = "bee ops // black + gold"
    CSS_PATH = "theme.tcss"

    def __init__(self) -> None:
        super().__init__()
        self.settings = Settings.load()

    def on_mount(self) -> None:
        self.push_screen(MainMenuScreen(self.settings))


def run_tui() -> None:
    PlArchApp().run()
