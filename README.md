# +55 Real Estate Global

Site de Avaliação da +55 Real Estate Global feito em Flask, Jinja e TailwindCSS.

## Comandos

```
pip install -r requirements.txt
python manage.py migrar
python manage.py semear
python wsgi.py
pytest
```

Para recompilar o CSS (só ao mexer nos templates): `npm install` e `npm run css`.

O servidor está pronto quando `GET /saude` responde 200. O arquivo `banca.json` declara os mesmos comandos.

## Variáveis de ambiente

Copie `example.env` para `.env` e preencha.

| Variável | Uso |
|---|---|
| PORT | Porta HTTP |
| DB_PATH ou DATABASE_URL | Banco SQLite |
| UPLOAD_DIR | Diretório das fotos enviadas |
| SESSAO_TTL_SEGUNDOS | Duração da sessão do painel |
| COOKIE_SECURE | `true` ou `false` |
| SEGREDO_APP | Segredo de assinatura da sessão, 32 bytes ou mais |
| ADMIN_EMAIL, ADMIN_SENHA | Conta inicial criada por `semear` |
| WHATSAPP_E164 | Número do WhatsApp, formato + e dígitos |
| NODE_ENV | `test` ou `production` |

## Ferramentas

| Ferramenta | Para que serve no projeto |
|---|---|
| Flask | Servidor HTTP, rotas e blueprints |
| Jinja2 | Templates com escape automático de HTML |
| SQLAlchemy | Mapeamento dos models e consultas |
| SQLite | Banco em arquivo local |
| Pydantic | Validação dos dados de entrada |
| pwdlib com Argon2 | Hash das senhas |
| python-jose | Assinatura do token de sessão (JWT) guardado em cookie HttpOnly |
| python-dotenv | Leitura do `.env` |
| livereload | Recarga automática em desenvolvimento |
| pytest | Testes unitários |
| Tailwind CSS 3 (CLI) | Compila o CSS de utilitários para `static/styles/tailwind.css` |
| Google Fonts | Fraunces e Instrument Sans |

## Estrutura

| Pasta ou arquivo | Conteúdo |
|---|---|
| `domain/` | Regras do catálogo, sem acesso a banco ou HTTP |
| `models/` | Tabelas SQLAlchemy |
| `schemas/` | Validação Pydantic |
| `services/` | Casos de uso: imóveis, fotos, páginas, login |
| `routes/` | Blueprints: site público, painel e API JSON |
| `libs/security/` | Hash de senha, token e limitador de tentativas |
| `migrations/` | SQL numerado, aplicado por `python manage.py migrar` |
| `data/` | CSV de imóveis, importador e pasta `Imagens/` com o índice das fotos |
| `templates/` e `static/` | HTML, CSS e JavaScript |
| `tests/` | Testes unitários |

## Classes

### Domínio (`domain/`)

| Classe | Responsabilidade |
|---|---|
| `Money` | Valor monetário imutável com `Decimal` e moeda (BRL, USD, AED). Calcula preço por m², converte para USD para ordenar e formata o texto. |
| `Place` | Praça (BR, PA, AE) com nome e moeda de negociação. |
| `Typology` | Classe abstrata de tipologia. Define campos obrigatórios, campos que não se aplicam e a área-base do preço por m². |
| `UnitTypology` | Herda de `Typology`. Exige área privativa, quartos e andar. Preço por m² sobre a área privativa. |
| `HouseTypology` | Herda de `Typology`. Exige área construída, área do terreno e quartos. Preço por m² sobre a área construída. |
| `Apartment`, `Penthouse` | Herdam de `UnitTypology`. |
| `Villa`, `Estate` | Herdam de `HouseTypology`. |

Funções do domínio: `rule_errors` aplica as regras do Anexo C (campos por tipologia e moeda por praça), `typology_for` devolve a tipologia, e o módulo `status` define as transições de situação, a visibilidade pública, o WhatsApp e a exigência de foto para publicar.

### Models (`models/`)

| Classe | Tabela | Conteúdo |
|---|---|---|
| `RealEstateModel` | `real_estate` | Imóvel, situação e data de venda. |
| `RealEstatePhotoModel` | `real_estate_photos` | Foto, descrição, ordem e marca de capa. Pertence a um imóvel (composição). |
| `UserModel` | `users` | Administrador, e-mail e hash da senha. |
| `SiteTextModel` | `site_texts` | Textos editáveis por página e campo. |
| `RevokedTokenModel` | `revoked_tokens` | Sessões encerradas ao sair. |

### Schemas (`schemas/`)

`RealEstateCreateSchema` valida os dados do imóvel. `UserLoginSchema` e `UserRegistrationSchema` validam login e cadastro de usuário. `SiteTextSchema` valida os textos editáveis. `PhotoMetadataSchema` descreve os metadados de foto.

### Serviços e bibliotecas

| Classe ou módulo | Responsabilidade |
|---|---|
| `LoginThrottle` | Bloqueia o login depois de 5 falhas seguidas em 15 minutos, por IP e e-mail. Fica em memória. |
| `services/real_estate.py` | Cadastro, edição, mudança de situação, fotos, listagem pública e preparo dos dados para API e templates. |
| `services/media.py` | Valida a foto pelo conteúdo (JPEG, PNG ou WebP, até 5 MB) e grava com nome gerado. |
| `services/pages.py` | Lê e salva os textos da Início e do rodapé. |
| `services/admin.py` | Autentica, emite e revoga a sessão. |
| `ValidationFailed`, `NotFound`, `UploadRejected` | Erros de domínio traduzidos em mensagens por campo ou códigos HTTP. |

## Rotas principais

| Rota | Descrição |
|---|---|
| `/`, `/imoveis`, `/imoveis/<slug>` | Site público. `/imoveis` aceita `?pais=BR|PA|AE` e `?ordenar=recentes|preco_asc|preco_desc`. |
| `/tese`, `/pracas`, `/diagnostico`, `/tokenizacao`, `/lista-de-espera`, `/governanca`, `/schedule/` | Páginas institucionais. |
| `/admin/login`, `/admin/real-estate`, `/admin/pages` | Painel, com sessão obrigatória. |
| `/api/v1/...` | API JSON do contrato do Anexo D. |
| `/media/<arquivo>` | Fotos enviadas. |
| `/saude` | Verificação de funcionamento. |

## Animações

O site público tem exatamente estas animações. Todas usam só `transform` ou `opacity` e param com "reduzir movimento".

| Animação | Onde | Propriedades |
|---|---|---|
| `animate-bounce` | Indicador "SCROLL" da Início | `transform` |
| `marquee` | Marquee da tela inicial | `transform` |

## Observações

- O limitador de tentativas de login fica em memória: não vale entre processos nem sobrevive a reinício.
- A ordenação por preço compara moedas por uma cotação fixa em `domain/money.py`, ela não puxa de nenhuma api ou lib.
