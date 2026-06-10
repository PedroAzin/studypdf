# StudyPDF Coach - Documentacao

Esta pasta documenta o que foi implementado no StudyPDF Coach depois da refatoracao em camadas e feature modules.

## Indice

- [Arquitetura](architecture.md)
- [Mapa de rotas](routes.md)
- [Casos de uso](use-cases/README.md)
- [Decisoes tecnicas](technical-decisions.md)

## Escopo atual

O sistema permite:

- Enviar PDFs para processamento em background.
- Guardar livros em uma estante com status, progresso e estatisticas.
- Ler o PDF convertido para HTML com imagens, capitulos, sumario lateral e progresso.
- Criar, listar, editar, remover, buscar e exportar notas.
- Reprocessar livros quando necessario.
- Receber eventos de processamento via SSE para atualizar a estante.

## Organizacao do codigo

```text
app.py                         # entrada da aplicacao
studypdf/
  app_factory.py               # cria Flask app, registra blueprints, filtros e erros
  config.py                    # constantes e caminhos
  db.py                        # infraestrutura SQLite
  domain/                      # regras puras e funcoes deterministicas
  pdf/                         # extracao e renderizacao de PDF
  services/                    # casos de uso e orquestracao de negocio
  routes/                      # blueprints HTTP por feature
templates/                     # telas Jinja
static/                        # CSS e JavaScript do frontend
```

