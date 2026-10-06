# Diário de Decisões

O diagrama de classes está no formato `.mermaid`.
Para você acessar a página de administrador, lembre de colocar `/admin` no url.

## Premissas que assumi

| # | Onde o enunciado ou as regras não diziam | O que assumi | Por quê |
|---|---|---|---|
| 1 | Sistema de Autenticação | Acesso a Banco de Dados com JWT e hashing com Argon | Permite com que sejam mantidos os usuários sejam mantidos de forma segura |
| 2 | Como comparar preços em moedas diferentes na ordenação | Converto tudo para dólar com uma cotação fixa | O enunciado não dá a cotação. Assim a lista nunca mistura moedas e a ordenação fica previsível |
| 3 | Imóvel sem preço Aceito sem preço como rascunho, mas só publica com preço | O contrato permite preço nulo, e um imóvel público sem preço desmoralizaria o catálogo |
| 4 | Moeda quando não é informada ou não bate com a praça | Se faltar, uso a moeda da praça. Se for outra, recuso | O Anexo C diz que o preço é cadastrado na moeda de negociação da praça |
| 5 | Formatos de preço e área da planilha | Escrevi um importador que normaliza tudo para número decimal | A planilha veio como cada praça enviou, então os formatos são diferentes |
| 6 | Quais mudanças de situação são permitidas | Rascunho, publicado, reservado, vendido e arquivado seguem uma tabela de transições. Vendido só vai para arquivado e nunca volta a ser oferecido | As regras só dizem que vendido não volta. O resto é a ordem natural do fluxo comercial |
| 7 | Imóvel reservado tem botão de WhatsApp? | Tem | A regra diz que publicado tem e vendido não. Reservado ainda pode ser negociado |
| 8 | O que fazer com fotos no imóvel já publicado | Não deixo remover a última foto de um imóvel visível | O Anexo C exige pelo menos uma foto para ir ao ar |
| 9 | Nome do arquivo da foto e tipo aceito | Gero um nome aleatório e identifico o tipo pelo conteúdo, não pela extensão | Nada que o usuário envie deve definir o nome ou o lugar do arquivo |
| 10 | Endereço (slug) de cada imóvel | Gero do título mais a referência | Fica legível e único, já que a referência não se repete |
| 11 | Quantas tentativas de login erradas são aceitas | Bloqueio depois de 5 falhas seguidas em 15 minutos, por IP e e-mail, guardado em memória | O enunciado pede resistência a tentativas repetidas, sem número. A limitação de memória está declarada na seção de segurança |
| 12 | Perfis no painel | Um único perfil de administrador | O enunciado deixa mais de um perfil fora de escopo |
| 13 | Quais textos são editáveis | Título, destaque e abertura da Início, e o texto do rodapé | O enunciado pede o campo mínimo `titulo` e o `texto` do rodapé, e deixa os outros campos livres |
| 14 | Quais imóveis aparecem em destaque na Início | Os 3 publicados mais recentes | O enunciado pede imóveis em destaque sem dizer o critério |
| 15 | Páginas além das quatro obrigatórias (Diagnóstico, Tokenização e outras) | Criei páginas só com o copy do Anexo A, e os formulários não gravam dados | O cabeçalho e o rodapé do copy têm esses links, e o enunciado deixa essas funções fora de escopo |

## Decisões

| # | Decisão | Alternativas que considerei | Por que descartei | Risco que aceitei |
|---|---|---|---|---|
| 1 | Usar Python | NodeJS/Vue/React | Eu não gosto de usar esse tipo de Linguagem e Framework para gerenciar Backend | Complicar o CSS e tornar o site inteiramente SSR. |
| 2 | Usar Flask | Django | Complicado de configurar e serve para projetos muito mais completos que o meu | Deixar a estrutura do código menos sólida. |
| 3 | Usar TailwindCSS | CSS normal | Simplifica e etapa de estruturação do código | Precisa de compilar posteriormente. |
| 4 | Usar SQLite | PostgreSQL/MySQL | Precisaria de um servidor à parte, e o enunciado pede que rode de graça em qualquer sistema | Não aguenta muitos acessos de escrita ao mesmo tempo. |
| 5 | Criar o banco com migrações SQL numeradas | `create_all` do SQLAlchemy | Sincronizar schema é proibido | |Ter que lembrar de fazer migração |
| 6 | Guardar o JWT em cookie HttpOnly | `localStorage` | Qualquer script da página consegue ler o `localStorage`, e o enunciado exige que a sessão não seja legível por script | Preciso tratar a proteção contra requisições de outra origem (CSRF), que fica como limitação. |
| 7 | Guardar os tokens encerrados em uma tabela | Deixar o JWT valer até expirar | Sair precisa encerrar o acesso na hora, e o JWT sozinho não tem como ser cancelado | Cada requisição do painel faz uma consulta a mais. |
| 8 | Usar Argon2 para as senhas | bcrypt/SHA-256 | SHA-256 é rápido demais para senha, e o Argon2 é o recomendado hoje | Pode consumir mais memória no login. |
| 9 | Usar `Decimal` para dinheiro | `float` | O `float` perde centavos e o contrato trafega valores como texto decimal | Preciso converter ao ler e ao gravar. |

## Herança e composição (R-10)

| Parte do domínio | Usei herança, composição ou outra forma | Por quê |
|---|---|---|
| Tipologias (Typology, UnitTypology, Estate, Penthouse ...) | Herança em Três Niveis / Vazias | A classe serve para definir tipos de imóveis e especificar regras para casos especificos.|
| Money | Composição | Evitar misturar moedas por engano e combina a conversão em um lugar só. |
| Place | Dados Imutáveis | Servem para determinar diferentes praças. |
| RealEstateModel / RealEstatePhotoModel | Composição por relacionamento | Determina a relação entre fotos e imóveis.
| LoginThrottle | Classe com Estado Interno | Guarda temporariamente tentativas por chave.

## Stack e bibliotecas

| Biblioteca ou recurso | O que faz por mim | Como verifiquei |
|---|---|---|
| Flask | Servidor HTTP, rotas, cookies e leitura de formulário multipart. | Rodei o fluxo todo pelo cliente de teste do Flask (login, cadastro, upload, publicação, sair) e conferi os status e o cookie. |
| SQLAlchemy | Mapeia as tabelas e monta as consultas. É um ORM completo, tolerado com condição. | As tabelas vêm de migrações SQL numeradas, e `migrar` as aplica em ordem. Para mostrar o SQL da listagem filtrada na defesa, ligar `echo=True` no `create_engine`. |
| SQLite | Banco em arquivo. | Abri o arquivo e conferi as tabelas e os valores semeados (preços, áreas e situações). |
| Migrações SQL (`migrations/` e `database_migrations.py`) | Cria e versiona o schema, sem sincronização automática. | Rodei `migrar` duas vezes: na segunda saiu "Nada a aplicar". Há teste de que o schema bate com os models. |
| Pydantic | Valida tipos e limites dos campos de entrada. | Testes com preço fora do formato, `float` no valor e ref inválida, que viram mensagem por campo. |
| pwdlib com Argon2 | Faz o hash da senha, com sal e custo. | Abrir a tabela `users` e ver que `hash_pwd` começa com `$argon2` e que a senha em texto não aparece. |
| python-jose | Assina e valida o token de sessão. | Token com `exp`; conferi que, depois de sair, o mesmo token deixa de funcionar (tabela `revoked_tokens`). |
| `LoginThrottle` | Bloqueia depois de 5 falhas seguidas. | Seis tentativas erradas: a sexta respondeu 429. Limitação conhecida: fica em memória. |
| python-dotenv | Lê o `.env`. | Subi o app com e sem variáveis e conferi o comportamento. |
| pytest | Roda os 70 testes unitários (dinheiro, tipologias, situações, serviço, importador e migrações). | Rodei `pytest` no projeto e num venv novo só com o `requirements.txt` fixado. |
| Tailwind CSS 3 (CLI) | Gera o CSS de utilitários compilado em `static/styles/tailwind.css`. É tolerado com condição: as cores vêm de tokens e, na defesa, você escreve em CSS puro um trecho pedido. | Rodei `npm run css`, conferi que as classes aparecem no arquivo e que as páginas carregam sem o script do CDN. |
| livereload | Recarrega a página em desenvolvimento. | Só é usado com `NODE_ENV=test`. |
| Google Fonts | Fraunces e Instrument Sans. | Conferi o carregamento no navegador. |

## Segurança: limitações que conheço

- A limitação de logins não é persistente nem permanente; Por mais que tenham diferentes `roles`, ambos podem fazer as mesmas coisas; O usuário pode ter acesso a tudo que esteja nos uploads desde que esteja lá.

## O que testei e como

- Migração, Cálculos de Dinheiro, Status de Imóvel, Tipologias e suas limitações e Serviço de imóveis.

## Onde errei ou mudei de ideia

- Tentei fazer um protótipo mais amplo do começo mas acabei supercomplicando e tentei me basear só no necessário, tentei fazer os modelos desde o início do que eu declarei no tópico `## O QUE EU FARIA COM MAIS TEMPO`.

## O que cortei e por quê

- Gerenciamento de contas, formulários e um overview completo; Falta de tempo.

## O que aprendi

- Gerenciamento de Imagens, Regex e Testes Automatizados (Esse eu ainda não entendi perfeitamente).

## O que eu faria com mais tempo

- Completaria a seção de administrador com overview, gerenciamento de contas, cadastro de contas novas e formulários que são enviados para o Backend e podem ser lidos pelos administradores.

## Uso de ferramentas de IA

| Ferramenta | Para quê | O que aproveitei | O que descartei e por quê |
|---|---|---|---|
| Gemini | Pesquisa | Usei para pesquisar layouts de HTML com TailwindCSS e uma organização de site mais completa | Evitei copiar e colar seções de código, aprendi alguns pontos escrevendo manualmente recomendações. |
| Claude | Documentação | Usei para documentar o código de forma mais prática. | Escrever seções que eu mesmo preciso escrever. (como essa) | 

## Tempo gasto

| Tarefa | Minutos |
|---|---|
| T0 · Leitura do enunciado e dos anexos | 50 minutos |
| T1 · Base, migrações e semear | 40 minutos |
| T2 · Domínio e testes | 50 minutos |
| T3 · Entrar, sair e proteger o painel | 30 minutos |
| T4 · Painel de imóveis | 2 horas 20 minutos |
| T5 · Fotos | 1 hora 20 minutos |
| T6 · Site público | 30 minutos |
| T7 · Textos editáveis | 50 minutos |
| T8 · Animações e checklist visual | 40 minutos |
| T9 · README, Diário e diagrama | 30 minutos |
| **Total** | 9 Horas |
