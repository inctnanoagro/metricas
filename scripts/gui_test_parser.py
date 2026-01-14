#!/usr/bin/env python3
"""
GUI para testar parsers Lattes.

Interface gráfica simples usando tkinter (stdlib) para:
- Selecionar arquivos HTML
- Rodar parse_fixture()
- Validar contra schema
- Exportar JSON
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from metricas_lattes.parser_router import parse_fixture, PARSER_REGISTRY


class ParserGUI:
    """GUI para testar parsers"""

    def __init__(self, root):
        self.root = root
        self.root.title("Lattes Parser - Test GUI")
        self.root.geometry("900x700")

        self.selected_files = []
        self.schema = None
        self.results = []

        self.setup_ui()
        self.load_schema()

    def setup_ui(self):
        """Setup interface"""
        # Top frame - File selection
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Arquivos HTML:").pack(side=tk.LEFT)

        self.files_label = ttk.Label(top_frame, text="Nenhum arquivo selecionado",
                                     foreground="gray")
        self.files_label.pack(side=tk.LEFT, padx=10)

        ttk.Button(top_frame, text="Selecionar HTML(s)",
                  command=self.select_files).pack(side=tk.RIGHT)

        # Options frame
        options_frame = ttk.Frame(self.root, padding="10")
        options_frame.pack(fill=tk.X)

        self.validate_schema_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Validar contra schema",
                       variable=self.validate_schema_var).pack(side=tk.LEFT)

        self.save_json_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Salvar JSON ao lado do HTML",
                       variable=self.save_json_var).pack(side=tk.LEFT, padx=20)

        # Run button
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill=tk.X)

        self.run_button = ttk.Button(button_frame, text="Rodar",
                                     command=self.run_parsing, state=tk.DISABLED)
        self.run_button.pack(side=tk.LEFT)

        self.export_button = ttk.Button(button_frame, text="Exportar Consolidado",
                                       command=self.export_consolidated,
                                       state=tk.DISABLED)
        self.export_button.pack(side=tk.LEFT, padx=10)

        ttk.Button(button_frame, text="Limpar Log",
                  command=self.clear_log).pack(side=tk.LEFT, padx=10)

        # Progress
        self.progress = ttk.Progressbar(button_frame, mode='indeterminate')
        self.progress.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=10)

        # Log area
        log_frame = ttk.Frame(self.root, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(log_frame, text="Log:").pack(anchor=tk.W)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=30,
                                                  font=("Courier", 10))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Status bar
        self.status_var = tk.StringVar(value="Pronto")
        status_bar = ttk.Label(self.root, textvariable=self.status_var,
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def load_schema(self):
        """Load JSON Schema"""
        schema_path = Path(__file__).parent.parent / 'schema' / 'producoes.schema.json'
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                self.schema = json.load(f)
            self.log(f"✓ Schema carregado: {schema_path.name}\n")
        except Exception as e:
            self.log(f"✗ Erro ao carregar schema: {e}\n")
            self.schema = None

    def select_files(self):
        """Select HTML files"""
        files = filedialog.askopenfilenames(
            title="Selecione arquivos HTML",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
        )

        if files:
            # Filter out AppleDouble files
            valid_files = [Path(f) for f in files if not Path(f).name.startswith('._')]

            self.selected_files = valid_files
            count = len(valid_files)

            self.files_label.config(
                text=f"{count} arquivo(s) selecionado(s)",
                foreground="blue"
            )
            self.run_button.config(state=tk.NORMAL)
            self.log(f"\n{'='*60}\n")
            self.log(f"Arquivos selecionados ({count}):\n")
            for f in valid_files:
                self.log(f"  - {f.name}\n")

    def run_parsing(self):
        """Run parsing on selected files"""
        if not self.selected_files:
            messagebox.showwarning("Aviso", "Selecione arquivos HTML primeiro")
            return

        self.run_button.config(state=tk.DISABLED)
        self.progress.start(10)
        self.results = []

        self.log(f"\n{'='*60}\n")
        self.log(f"INICIANDO PARSING\n")
        self.log(f"Data/hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.log(f"{'='*60}\n\n")

        for idx, filepath in enumerate(self.selected_files, 1):
            self.status_var.set(f"Processando {idx}/{len(self.selected_files)}: {filepath.name}")
            self.root.update()

            try:
                self.process_file(filepath)
            except Exception as e:
                self.log(f"✗ ERRO FATAL em {filepath.name}: {e}\n\n")

        self.progress.stop()
        self.run_button.config(state=tk.NORMAL)
        self.export_button.config(state=tk.NORMAL)
        self.status_var.set(f"Pronto - {len(self.results)} arquivo(s) processado(s)")

        self.log(f"\n{'='*60}\n")
        self.log(f"CONCLUSÃO\n")
        self.log(f"Total processado: {len(self.results)}\n")
        self.log(f"{'='*60}\n")

    def process_file(self, filepath: Path):
        """Process a single file"""
        self.log(f"{'─'*60}\n")
        self.log(f"Arquivo: {filepath.name}\n")

        # Parse
        try:
            result = parse_fixture(filepath)
        except Exception as e:
            self.log(f"✗ Erro ao parsear: {e}\n\n")
            return

        # Show info
        parser_type = self.guess_parser_type(filepath)
        self.log(f"Parser: {parser_type}\n")
        self.log(f"Items extraídos: {len(result['items'])}\n")

        # Validate schema
        if self.validate_schema_var.get() and self.schema:
            errors = self.validate_result(result)
            if errors:
                self.log(f"✗ Validação de schema: {len(errors)} erro(s)\n")
                for error in errors[:5]:  # Show first 5
                    self.log(f"  - {error}\n")
                if len(errors) > 5:
                    self.log(f"  ... e mais {len(errors) - 5} erro(s)\n")
            else:
                self.log(f"✓ Validação de schema: OK\n")
        else:
            self.log(f"⊘ Validação de schema: PULADA\n")

        # Save JSON
        if self.save_json_var.get():
            output_path = filepath.with_suffix('.parsed.json')
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                self.log(f"✓ JSON salvo: {output_path.name}\n")
            except Exception as e:
                self.log(f"✗ Erro ao salvar JSON: {e}\n")

        self.results.append({
            'filepath': str(filepath),
            'filename': filepath.name,
            'result': result,
            'parser_type': parser_type
        })

        self.log("\n")

    def guess_parser_type(self, filepath: Path) -> str:
        """Guess which parser was used"""
        from metricas_lattes.parser_router import normalize_filename

        normalized = normalize_filename(filepath.name)

        for pattern in PARSER_REGISTRY.keys():
            if pattern in normalized:
                return f"{PARSER_REGISTRY[pattern].__name__} (specific)"

        return "GenericParser (fallback)"

    def validate_result(self, data: dict) -> list:
        """Validate result against schema"""
        try:
            from jsonschema import Draft7Validator
        except ImportError:
            try:
                from jsonschema import Draft202012Validator as Draft7Validator
            except ImportError:
                return ["jsonschema não instalado"]

        validator = Draft7Validator(self.schema)
        errors = []

        for error in validator.iter_errors(data):
            path = '.'.join(str(p) for p in error.path) if error.path else 'root'
            errors.append(f"{path}: {error.message}")

        return errors

    def export_consolidated(self):
        """Export consolidated JSON"""
        if not self.results:
            messagebox.showwarning("Aviso", "Nenhum resultado para exportar")
            return

        output_path = filedialog.asksaveasfilename(
            title="Salvar JSON consolidado",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if not output_path:
            return

        try:
            consolidated = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'total_files': len(self.results),
                    'total_items': sum(len(r['result']['items']) for r in self.results)
                },
                'results': self.results
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(consolidated, f, indent=2, ensure_ascii=False)

            self.log(f"\n✓ JSON consolidado salvo: {Path(output_path).name}\n")
            messagebox.showinfo("Sucesso", f"JSON consolidado salvo:\n{output_path}")

        except Exception as e:
            self.log(f"\n✗ Erro ao salvar consolidado: {e}\n")
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")

    def clear_log(self):
        """Clear log"""
        self.log_text.delete(1.0, tk.END)

    def log(self, message: str):
        """Add message to log"""
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.root.update()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = ParserGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
