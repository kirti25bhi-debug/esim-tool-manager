"""Graphical User Interface for eSim Automated Tool Manager (Tkinter based)."""

import os
import sys
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Optional

from esim_tool_manager.core.config_manager import ConfigManager
from esim_tool_manager.core.dependency_checker import DependencyChecker
from esim_tool_manager.core.installer import ToolInstaller
from esim_tool_manager.core.logger import get_logger, get_memory_log_handler
from esim_tool_manager.core.models import ToolStatus
from esim_tool_manager.core.registry import ToolRegistry
from esim_tool_manager.core.updater import ToolUpdater
from esim_tool_manager.platforms.base import BasePlatformManager


class ToolManagerGUI:
    """Modern Tkinter GUI for managing eSim external tools and dependencies."""

    def __init__(
        self,
        root: tk.Tk,
        registry: ToolRegistry,
        platform_mgr: BasePlatformManager,
    ):
        self.root = root
        self.registry = registry
        self.platform_mgr = platform_mgr
        self.logger = get_logger()
        self.installer = ToolInstaller(registry, platform_mgr)
        self.updater = ToolUpdater(registry, platform_mgr)
        self.config_mgr = ConfigManager(registry, platform_mgr)
        self.checker = DependencyChecker(registry, platform_mgr)

        self.root.title("eSim Automated Tool Manager")
        self.root.geometry("900x640")
        self.root.minsize(780, 520)

        self._apply_styles()
        self._build_header()
        self._build_notebook()
        self._build_statusbar()
        self._attach_log_listener()

        # Load data in background thread
        self.refresh_tools_async()

    def _apply_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("TNotebook.Tab", font=("Helvetica", 11, "bold"), padding=[12, 6])
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))
        style.configure("Treeview", font=("Helvetica", 10), rowheight=26)
        style.configure("Accent.TButton", font=("Helvetica", 10, "bold"), foreground="#0066cc")

    def _build_header(self):
        header_frame = tk.Frame(self.root, bg="#1a365d", height=70)
        header_frame.pack(side=tk.TOP, fill=tk.X)

        title_lbl = tk.Label(
            header_frame,
            text="⚡ eSim Automated Tool Manager",
            font=("Helvetica", 16, "bold"),
            fg="white",
            bg="#1a365d",
        )
        title_lbl.pack(side=tk.LEFT, padx=16, pady=12)

        self.platform_badge = tk.Label(
            header_frame,
            text=f"Platform: {self.platform_mgr.get_platform_key().upper()} | Python {sys.version.split()[0]}",
            font=("Helvetica", 10),
            fg="#cbd5e0",
            bg="#1a365d",
        )
        self.platform_badge.pack(side=tk.RIGHT, padx=16, pady=16)

    def _build_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Tab 1: Tools Catalog & Management
        self.tab_tools = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_tools, text="  🛠️ Tools & Status  ")
        self._setup_tools_tab()

        # Tab 2: Doctor & Dependencies
        self.tab_doctor = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_doctor, text="  🩺 eSim Doctor  ")
        self._setup_doctor_tab()

        # Tab 3: Configuration & Environment
        self.tab_config = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_config, text="  ⚙️ Configuration  ")
        self._setup_config_tab()

        # Tab 4: Logs
        self.tab_logs = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_logs, text="  📜 Action Logs  ")
        self._setup_logs_tab()

    def _setup_tools_tab(self):
        # Action Bar
        btn_bar = tk.Frame(self.tab_tools, bg="#f7fafc", pady=8)
        btn_bar.pack(fill=tk.X)

        btn_refresh = ttk.Button(btn_bar, text="🔄 Refresh", command=self.refresh_tools_async)
        btn_refresh.pack(side=tk.LEFT, padx=6)

        btn_install_missing = ttk.Button(
            btn_bar, text="⬇️ Install All Missing", command=self.install_all_async
        )
        btn_install_missing.pack(side=tk.LEFT, padx=6)

        btn_update_all = ttk.Button(
            btn_bar, text="🚀 Upgrade Outdated", command=self.update_all_async
        )
        btn_update_all.pack(side=tk.LEFT, padx=6)

        # Tools Treeview Table
        cols = ("id", "name", "category", "installed_ver", "recommended", "status")
        self.tree = ttk.Treeview(self.tab_tools, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("id", text="Tool ID")
        self.tree.heading("name", text="Tool Name")
        self.tree.heading("category", text="Category")
        self.tree.heading("installed_ver", text="Installed Ver")
        self.tree.heading("recommended", text="Target Ver")
        self.tree.heading("status", text="Health / Status")

        self.tree.column("id", width=90)
        self.tree.column("name", width=200)
        self.tree.column("category", width=140)
        self.tree.column("installed_ver", width=100)
        self.tree.column("recommended", width=90)
        self.tree.column("status", width=180)

        scrollbar = ttk.Scrollbar(self.tab_tools, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Context Action Controls
        action_frame = tk.Frame(self.tab_tools, pady=6)
        action_frame.pack(fill=tk.X, padx=6)

        self.btn_install_sel = ttk.Button(
            action_frame, text="Install Selected", command=self._on_install_selected
        )
        self.btn_install_sel.pack(side=tk.LEFT, padx=4)

        self.btn_update_sel = ttk.Button(
            action_frame, text="Update Selected", command=self._on_update_selected
        )
        self.btn_update_sel.pack(side=tk.LEFT, padx=4)

    def _setup_doctor_tab(self):
        doc_bar = tk.Frame(self.tab_doctor, bg="#f7fafc", pady=8)
        doc_bar.pack(fill=tk.X)

        btn_run_doctor = ttk.Button(doc_bar, text="🩺 Run Diagnostics", command=self.run_doctor_async)
        btn_run_doctor.pack(side=tk.LEFT, padx=8)

        self.doctor_text = tk.Text(self.tab_doctor, wrap=tk.WORD, font=("Courier", 10), padx=8, pady=8)
        scroll = ttk.Scrollbar(self.tab_doctor, orient=tk.VERTICAL, command=self.doctor_text.yview)
        self.doctor_text.configure(yscroll=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.doctor_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _setup_config_tab(self):
        cfg_bar = tk.Frame(self.tab_config, bg="#f7fafc", pady=8)
        cfg_bar.pack(fill=tk.X)

        btn_save_cfg = ttk.Button(
            cfg_bar, text="💾 Generate & Export Config", command=self.generate_config
        )
        btn_save_cfg.pack(side=tk.LEFT, padx=8)

        self.config_text = tk.Text(self.tab_config, wrap=tk.NONE, font=("Courier", 10), padx=8, pady=8)
        scroll_y = ttk.Scrollbar(self.tab_config, orient=tk.VERTICAL, command=self.config_text.yview)
        scroll_x = ttk.Scrollbar(self.tab_config, orient=tk.HORIZONTAL, command=self.config_text.xview)
        self.config_text.configure(yscroll=scroll_y.set, xscroll=scroll_x.set)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.config_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _setup_logs_tab(self):
        log_bar = tk.Frame(self.tab_logs, bg="#f7fafc", pady=6)
        log_bar.pack(fill=tk.X)

        btn_clear = ttk.Button(log_bar, text="Clear Log", command=self._clear_logs)
        btn_clear.pack(side=tk.LEFT, padx=6)

        self.log_text = tk.Text(self.tab_logs, wrap=tk.WORD, bg="#1a202c", fg="#e2e8f0", font=("Menlo", 9), padx=6, pady=6)
        scroll = ttk.Scrollbar(self.tab_logs, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscroll=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

    def _build_statusbar(self):
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=("Helvetica", 9),
            padx=8,
            pady=4,
            bg="#edf2f7",
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _attach_log_listener(self):
        handler = get_memory_log_handler()
        if handler:
            handler.subscribe(self._on_new_log)

    def _on_new_log(self, msg: str):
        self.root.after(0, lambda: self._append_log(msg))

    def _append_log(self, msg: str):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def _clear_logs(self):
        self.log_text.delete("1.0", tk.END)

    def refresh_tools_async(self):
        self.status_var.set("Scanning installed tools...")
        threading.Thread(target=self._worker_refresh_tools, daemon=True).start()

    def _worker_refresh_tools(self):
        data = []
        for tool_def in self.registry.get_all_tools():
            info = self.registry.inspect_tool(tool_def, self.platform_mgr)
            data.append((
                tool_def.id,
                tool_def.name,
                tool_def.category.value,
                info.detected_version or "Not installed",
                tool_def.recommended_version,
                info.status.value,
            ))

        self.root.after(0, lambda: self._update_tree(data))

    def _update_tree(self, data):
        self.tree.delete(*self.tree.get_children())
        for row in data:
            self.tree.insert("", tk.END, values=row)
        self.status_var.set(f"Refreshed. {len(data)} tools in catalog.")

    def _get_selected_tool_id(self) -> Optional[str]:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a tool from the table.")
            return None
        return self.tree.item(selected[0])["values"][0]

    def _on_install_selected(self):
        tid = self._get_selected_tool_id()
        if tid:
            self.status_var.set(f"Installing {tid}...")
            threading.Thread(target=lambda: self._worker_install(tid), daemon=True).start()

    def _worker_install(self, tool_id: str):
        res = self.installer.install_tool(tool_id)
        self.root.after(0, lambda: messagebox.showinfo(
            "Installation Result", f"{res.action.title()} {tool_id}: {'Success' if res.success else 'Failed'}\n{res.message}"
        ))
        self.refresh_tools_async()

    def _on_update_selected(self):
        tid = self._get_selected_tool_id()
        if tid:
            self.status_var.set(f"Updating {tid}...")
            threading.Thread(target=lambda: self._worker_update(tid), daemon=True).start()

    def _worker_update(self, tool_id: str):
        res = self.updater.update_tool(tool_id)
        self.root.after(0, lambda: messagebox.showinfo(
            "Update Result", f"Update {tool_id}: {'Success' if res.success else 'Failed'}\n{res.message}"
        ))
        self.refresh_tools_async()

    def install_all_async(self):
        self.status_var.set("Installing missing tools...")
        threading.Thread(target=self._worker_install_all, daemon=True).start()

    def _worker_install_all(self):
        results = self.installer.install_all(required_only=True)
        summary = "\n".join([f"{k}: {'OK' if v.success else 'Failed'}" for k, v in results.items()])
        self.root.after(0, lambda: messagebox.showinfo("Install All Completed", f"Results:\n{summary or 'No missing tools.'}"))
        self.refresh_tools_async()

    def update_all_async(self):
        self.status_var.set("Upgrading outdated tools...")
        threading.Thread(target=self._worker_update_all, daemon=True).start()

    def _worker_update_all(self):
        results = self.updater.update_all()
        summary = "\n".join([f"{k}: {'OK' if v.success else 'Failed'}" for k, v in results.items()])
        self.root.after(0, lambda: messagebox.showinfo("Update All Completed", f"Results:\n{summary or 'All tools up to date.'}"))
        self.refresh_tools_async()

    def run_doctor_async(self):
        self.status_var.set("Running diagnostics...")
        threading.Thread(target=self._worker_run_doctor, daemon=True).start()

    def _worker_run_doctor(self):
        report = self.checker.run_diagnostics()
        lines = [
            "=" * 65,
            "               eSim Tool Manager Doctor Diagnostics",
            "=" * 65,
            f"OS:               {report.os_name} {report.os_version} ({report.architecture})",
            f"Python:           {report.python_version}",
            f"Package Manager:  {report.package_manager or 'None detected'}",
            f"Status:           {'ALL SYSTEMS HEALTHY' if report.all_healthy else 'ISSUES DETECTED'}",
            "-" * 65,
            f"{'Component':<22} {'Category':<16} {'Installed':<10} {'Status':<16}",
            "-" * 65,
        ]

        for item in report.tools:
            inst = "Yes" if item.installed else "No"
            lines.append(f"{item.name[:21]:<22} {item.category.value[:15]:<16} {inst:<10} {item.status.value:<16}")

        lines.append("-" * 65)

        if report.issues:
            lines.append("\nISSUES DETECTED:")
            for issue in report.issues:
                lines.append(f"  [X] {issue}")
            lines.append("\nRECOMMENDED REMEDIATIONS:")
            for rec in report.recommendations:
                lines.append(f"  -> {rec}")
        else:
            lines.append("\n[OK] All external tools, Python libraries, and environment settings are ready for eSim!")

        output = "\n".join(lines)
        self.root.after(0, lambda: self._render_doctor_report(output))

    def _render_doctor_report(self, text: str):
        self.doctor_text.delete("1.0", tk.END)
        self.doctor_text.insert(tk.END, text)
        self.status_var.set("Doctor diagnostics completed.")

    def generate_config(self):
        payload = self.config_mgr.save_configuration()
        env_vars = payload.get("environment_variables", {})
        lines = [
            f"# Generated eSim Configuration ({payload.get('generated_at')})",
            f"# Config File: {self.config_mgr.config_file}",
            f"# Script: {self.config_mgr.config_dir / 'esim_env.sh'}",
            "",
            "ENVIRONMENT VARIABLES:",
        ]
        for k, v in env_vars.items():
            lines.append(f"  {k} = {v}")

        self.config_text.delete("1.0", tk.END)
        self.config_text.insert(tk.END, "\n".join(lines))
        self.status_var.set(f"Configuration written to {self.config_mgr.config_file}")
        messagebox.showinfo("Configuration Exported", f"Successfully wrote:\n{self.config_mgr.config_file}\n{self.config_mgr.config_dir / 'esim_env.sh'}")


def launch_gui(registry: ToolRegistry, platform_mgr: BasePlatformManager):
    """Entry point for GUI application."""
    root = tk.Tk()
    app = ToolManagerGUI(root, registry, platform_mgr)
    root.mainloop()
