# StudyPDF Coach

MVP Flask para estudar PDFs tecnicos no navegador: upload, extracao por pagina com imagens, links para capitulos, leitura em HTML, notas vinculadas a trechos, busca e exportacao de contexto em Markdown para IA.

## Como subir o projeto

### 1. Preparar Supabase

Crie ou use um projeto Supabase com:

- PostgreSQL ativo.
- Um bucket privado no Storage chamado `studypdf`.
- Uma secret key de backend em `Project Settings > API > Secret keys`.

O bucket deve ficar privado. O app acessa o Storage pelo backend usando `SUPABASE_SERVICE_ROLE_KEY`.

### 2. Configurar `.env`

Crie/preencha o arquivo `.env` na raiz do projeto. Ele nao e versionado pelo Git.

```env
STUDYPDF_DATABASE_URL=postgresql://postgres:SENHA_URL_ENCODED@db.SEUPROJETO.supabase.co:5432/postgres?sslmode=require
SUPABASE_URL=https://SEUPROJETO.supabase.co
SUPABASE_SERVICE_ROLE_KEY=COLE_A_SECRET_KEY_AQUI
STUDYPDF_STORAGE_BUCKET=studypdf
STUDYPDF_SIGNING_KEY=TROQUE_POR_UMA_STRING_LONGA_ALEATORIA
STUDYPDF_UNDERSTANDING_CHECKS=1
```

Se a senha do banco tiver caracteres especiais, use URL encoding antes de colocar em `STUDYPDF_DATABASE_URL`.

### 3. Instalar dependencias

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

No Git Bash:

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

### 4. Rodar localmente

```powershell
python app.py
```

Acesse `http://127.0.0.1:5000`.

O app carrega `.env` automaticamente via `python-dotenv`. PDFs e assets ficam no Supabase Storage; o campo `books.file_path` guarda a chave do arquivo no bucket. O projeto nao usa `data/` nem `books/` como estado local persistente.

## Testes e cobertura

Para preparar o ambiente de desenvolvimento e rodar a suite com cobertura:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:STUDYPDF_TEST_DATABASE_URL="postgresql://postgres.../postgres?sslmode=require"
.\.venv\Scripts\python.exe -m pytest
```

Use uma instancia/schema de teste: a suite limpa as tabelas antes de cada teste.

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
  --sonar-sources=studypdf,app.py,static `
  --sonar-tests=tests `
  --sonar-python-coverage-report-paths=coverage.xml `
  --sonar-coverage-exclusions=static/** `
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
