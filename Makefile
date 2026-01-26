package:
	./scripts/package_clean.sh metricas-final-validation
	mv metricas-final-validation.tar.gz ~/Downloads/
	@echo "✅ Pacote em ~/Downloads/metricas-final-validation.tar.gz"

help:
	@echo "Comandos disponíveis:"
	@echo "  make help             - Lista comandos"
	@echo "  make package          - Gera pacote final em ~/Downloads"
	@echo "  make testar           - Executa scripts/testar.sh"
	@echo "  make testar-dry       - Executa scripts/testar.sh --dry-run"
	@echo "  make publicar         - Pipeline completo (batch + validation_pack + sync)"
	@echo "  make publicar-dry     - Apenas batch (dry_run)"
	@echo "  make publicar-nosync  - Batch + validation_pack (sem sync)"
	@echo "  make publicar-novalid - Batch + sync (sem validation_pack)"
	@echo "  make serve-docs       - Servidor local para docs/validacao"

testar:
	./scripts/testar.sh

testar-dry:
	./scripts/testar.sh --dry-run

publicar:
	./scripts/publicar_validacao.sh

publicar-dry:
	./scripts/publicar_validacao.sh --dry-run

publicar-nosync:
	./scripts/publicar_validacao.sh --no-sync

publicar-novalid:
	./scripts/publicar_validacao.sh --no-validation

serve-docs:
	@echo "Servindo em http://localhost:8000/docs/validacao/?prefill=<lattes_id>"
	@echo "Lista: http://localhost:8000/docs/validacao/lista.html"
	python3 -m http.server
