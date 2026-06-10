# StudyPDF Coach

MVP Flask para estudar PDFs tecnicos no navegador: upload, extracao por pagina com imagens, links para capitulos, leitura em HTML, notas vinculadas a trechos, busca e exportacao de contexto em Markdown para IA.

## Como rodar

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Acesse `http://127.0.0.1:5000`.

## Testes e cobertura

Para preparar o ambiente de desenvolvimento e rodar a suite com cobertura:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
```

O projeto exige no minimo 80% de cobertura via `pytest.ini`.

## Enviar analise para o Sonar

Com a instancia local do SonarQube rodando em `http://localhost:9000`, gere um token no Sonar e exporte em uma variavel de ambiente antes de executar o scan:

```powershell
$env:SONAR_TOKEN="seu-token"
.\scripts\sonar-scan.ps1
```

O script executa `pytest` antes do envio para gerar `coverage.xml`, que e importado pelo Sonar como cobertura Python.

O script usa por padrao:

- host: `http://localhost:9000`
- project key: `StudyPDF`
- quality gate: aguardado ao final da analise

Para sobrescrever host ou chave do projeto:

```powershell
$env:SONAR_TOKEN="seu-token"
.\scripts\sonar-scan.ps1 -SonarHostUrl "http://localhost:9000" -ProjectKey "StudyPDF"
```

Tambem e possivel rodar diretamente com `pysonar`:

```powershell
.\.venv\Scripts\pysonar.exe `
  --sonar-host-url=http://localhost:9000 `
  --sonar-token=$env:SONAR_TOKEN `
  --sonar-project-key=StudyPDF `
  --sonar-project-name=StudyPDF `
  --sonar-sources=studypdf,app.py `
  --sonar-tests=tests `
  --sonar-python-coverage-report-paths=coverage.xml `
  --sonar-python-version=3.14 `
  --sonar-qualitygate-wait
```

## Rotas principais

- `GET /`
- `GET /books`
- `POST /books/upload`
- `GET /books/<book_id>/read`
- `POST /books/<book_id>/reprocess`
- `GET /books/<book_id>/notes`
- `GET /notes/<note_id>`
- `POST /api/notes`
- `GET /api/search?q=`
- `GET /api/notes/<note_id>/export`
