import json
import subprocess
import os
from pathlib import Path

# Paths
MANIFEST_PATH = Path("docs/prefill/manifest.json")
MAILER_PATH = Path(os.path.expanduser("~/.openclaw/workspace-main/scripts/gmail_send.py"))
ENV_PATH = Path(os.path.expanduser("~/.openclaw/secrets/gmail.env"))

def load_researchers():
    with open(MANIFEST_PATH, "r") as f:
        data = json.load(f)
    
    researchers = []
    for lattes_id, filename in data.get("by_lattes_id", {}).items():
        # Filename format: id__slug-name.json
        parts = filename.replace(".json", "").split("__")
        if len(parts) > 1:
            slug = parts[1]
            name = slug.replace("-", " ").title()
            # Fix specific capitalizations if needed, but title case is usually ok
            researchers.append({"name": name, "id": lattes_id})
    
    # Sort by name
    researchers.sort(key=lambda x: x["name"])
    return researchers

def generate_html(researchers):
    list_html = "<ul>"
    for r in researchers:
        url = f"https://inctnanoagro.github.io/metricas/validacao/?prefill={r['id']}"
        # Exibe o link explícito para facilitar cópia
        list_html += f"<li><strong>{r['name']}</strong>:<br><a href='{url}'>{url}</a></li>"
    list_html += "</ul>"

    return f"""
    <html>
    <body>
        <p>Prezados pesquisadores,</p>
        
        <p>Estamos consolidando os indicadores do <strong>INCT NanoAgro</strong> para o relatório anual (período base 2024-2025).</p>
        
        <p>Para garantir a precisão dos dados, geramos uma prévia automática a partir dos Currículos Lattes. Precisamos que cada um valide quais produções devem ser oficialmente contabilizadas para o Instituto.</p>
        
        <h3>Como realizar a validação (Passo a Passo):</h3>
        <ol>
            <li>Encontre seu nome na lista abaixo e <strong>clique no link</strong> (ou copie e cole no navegador).</li>
            <li>Você verá suas produções filtradas para 2024-2025.</li>
            <li>Na coluna <strong>"INCT?"</strong>, marque a caixa de seleção para cada item que pertence ao INCT.</li>
            <li>Se necessário, use o botão "Editar" para corrigir dados.</li>
            <li>Ao finalizar, clique no botão <strong>"Baixar validação (JSON)"</strong> no topo da página.</li>
            <li><strong>Responda a este e-mail anexando o arquivo <code>.json</code> baixado.</strong></li>
        </ol>
        
        <hr>
        <h3>Links Individuais de Validação</h3>
        {list_html}
        <hr>
        
        <p>Dúvidas, estou à disposição.</p>
        
        <p>Atenciosamente,<br>
        <strong>Bruno Perez</strong><br>
        Gestão INCT NanoAgro</p>
    </body>
    </html>
    """

def send_email():
    researchers = load_researchers()
    html_content = generate_html(researchers)
    
    cmd = [
        "python3", str(MAILER_PATH),
        "--env-file", str(ENV_PATH),
        "--to", "bruno.perez@unesp.br",
        "--subject", "[Ação Necessária] Validação de Produção Científica (2024-2025) - INCT NanoAgro",
        "--html", html_content,
        "--text", "Por favor, abra este e-mail em um cliente compatível com HTML para ver os links de validação."
    ]
    
    print("Enviando e-mail...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Sucesso! E-mail enviado para bruno.perez@unesp.br")
    else:
        print("Erro ao enviar:")
        print(result.stderr)

if __name__ == "__main__":
    send_email()
