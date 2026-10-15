1 INTRODUÇÃO

A elaboração de um Trabalho de Conclusão de Curso (TCC) exige que o estudante de graduação da Universidade Estadual do Piauí (UESPI) realize, logo nas etapas iniciais, um levantamento bibliográfico que sustente o tema escolhido. Esse levantamento depende de fontes abertas e confiáveis, e a produção científica disponível em acesso aberto está distribuída em plataformas independentes, cada uma com sua própria interface, lógica de busca e estrutura de dados.

Os repositórios institucionais e o movimento de acesso aberto ampliaram a disponibilidade de literatura científica gratuita. Apesar desse avanço, o estudante que precisa consultar CORE, SciELO, OpenAlex e os repositórios institucionais da UESPI, da UFPI e da Biblioteca Digital Brasileira de Teses e Dissertações (BDTD) repete a mesma pergunta em vários sistemas, compara resultados duplicados e organiza manualmente as referências encontradas. Esse trabalho repetitivo consome tempo que poderia ser dedicado à leitura e à análise dos textos.

Diante dessa situação, a questão que orienta esta pesquisa é: como uma aplicação web pode contribuir para que estudantes de graduação da UESPI localizem, em uma única consulta, trabalhos acadêmicos disponíveis em múltiplos repositórios de acesso aberto?

O objeto de pesquisa deste trabalho é o projeto, a modelagem e o desenvolvimento de uma aplicação web que centraliza a busca em CORE, SciELO, OpenAlex e nos repositórios institucionais da UESPI, da UFPI e da BDTD. A integração utiliza, prioritariamente, interfaces programáticas e o protocolo OAI-PMH, e recorre à raspagem de dados (web scraping) apenas como complemento, para completar campos que as fontes não trazem em seus metadados, como o resumo. A aplicação oferece busca unificada por tema ou pelo nome do autor, filtros por ano e tipo de publicação, favoritos, exportação de resultados em formatos usados por gerenciadores de referências e uma API pública.

A justificativa para a pesquisa está na necessidade prática de simplificar a descoberta de literatura científica no ambiente universitário. Uma ferramenta gratuita, de acesso pelo navegador, que reúna os resultados e entregue as referências em formato reutilizável reduz o esforço de triagem e favorece a autonomia do estudante. Por ser uma aplicação exclusivamente web, ela deve funcionar de maneira adequada em computadores, tablets e celulares, sem exigir instalação.

O objetivo geral é desenvolver uma aplicação web que centralize a busca por trabalhos acadêmicos nas fontes CORE, SciELO, OpenAlex e nos repositórios institucionais da UESPI, da UFPI e da BDTD, apresentando os resultados de forma unificada, acessível e passível de exportação. Para alcançá-lo, a metodologia compreende o levantamento bibliográfico, o mapeamento de requisitos, a modelagem do sistema e a construção de um protótipo por etapas incrementais, implementado com Python e FastAPI no servidor, PostgreSQL para persistência e HTML5, CSS3 e JavaScript na interface.

Espera-se que o protótipo resultante contribua para a rotina de pesquisa dos estudantes da UESPI e sirva de base para evoluções futuras desenvolvidas pelo corpo discente do curso de Tecnólogo em Sistemas para a Internet.

2 REFERENCIAL TEÓRICO

2.1 PESQUISA ACADÊMICA E ACESSO ABERTO NO BRASIL

Segundo Lynch (2003), os repositórios institucionais são sistemas voltados ao armazenamento, à curadoria, à preservação e à disseminação de longo prazo da produção intelectual de universidades e centros de pesquisa. De acordo com Suber (2012), o acesso aberto consiste na remoção das barreiras financeiras historicamente associadas à leitura de periódicos científicos, o que amplia o acesso ao conhecimento produzido em instituições de pesquisa.

No Brasil, o Manifesto Brasileiro de Apoio ao Acesso Livre à Informação Científica (IBICT, 2005) afirma que a informação científica é insumo básico para o desenvolvimento científico e tecnológico de uma nação, defende que pesquisadores financiados com recursos públicos depositem suas obras em repositórios de acesso aberto e propõe que as instituições acadêmicas criem repositórios e incentivem a participação dos pesquisadores.

Segundo Packer (1998), o SciELO (Scientific Electronic Library Online) foi desenvolvido entre 1997 e 1998, com apoio da FAPESP e em parceria com a BIREME, para preparar, armazenar, publicar e avaliar periódicos científicos em ambiente eletrônico, com o objetivo de aumentar a visibilidade das revistas de países em desenvolvimento.

A Resolução CEPEX nº 034/2024 (UESPI, 2024) instituiu o repositório institucional de trabalhos acadêmicos da Universidade Estadual do Piauí, a ser gerenciado pela Biblioteca Central, com a finalidade de “armazenar, preservar, organizar e permitir o amplo acesso do repertório da produção intelectual”, e determina que o aluno deposite seu trabalho em PDF por meio do SIGAA.

Almeida e Dias (2023) descrevem a Biblioteca Digital Brasileira de Teses e Dissertações (BDTD) como uma biblioteca criada e mantida pelo Instituto Brasileiro de Informação em Ciência e Tecnologia (IBICT) e lançada oficialmente em 2002. Segundo os autores, os dados da BDTD são coletados via protocolo OAI-PMH a partir de um conjunto de metadados obrigatórios, e o padrão atual, o MTD-BR3, é composto por 28 metadados, dos quais 18 são obrigatórios.

2.2 REPOSITÓRIOS, INTEROPERABILIDADE E COLETA DE DADOS

Segundo Knoth e Zdrahal (2012), o CORE é um agregador de artigos em acesso aberto que reúne trabalhos de vários repositórios e os oferece em três níveis de acesso: recuperação de documentos individuais, análise de coleções e disponibilização de dados brutos por meio de APIs. Priem, Piwowar e Orr (2022) descrevem o OpenAlex como um índice aberto de obras, autores, periódicos, instituições e conceitos, sucessor do Microsoft Academic Graph, acessível por interface web, arquivos de dados e API REST.

Conforme Lagoze et al. (2002), o protocolo OAI-PMH (Open Archives Initiative Protocol for Metadata Harvesting) normatiza a coleta de metadados entre provedores de dados e provedores de serviços, o que permite que sistemas heterogêneos troquem registros de forma padronizada.

Almeida e Dias (2023) analisaram os mecanismos de busca dos repositórios de 51 instituições federais de ensino superior que participam da BDTD e registram que o TEDE2, sistema voltado ao armazenamento de teses e dissertações, está customizado na interface JSPUI do DSpace.

Chan e Zeng (2006) tratam a interoperabilidade de metadados no nível do esquema, por meio de mapeamentos semânticos entre campos equivalentes, e Zeng e Chan (2006) a tratam nos níveis do registro e do repositório, que envolvem a conversão e a consolidação dos dados.

De acordo com Vargiu e Urru (2012), o web scraping consiste no uso de algoritmos para extrair informações públicas de páginas HTML, o que permite coletar dados de fontes que não dispõem de interface programática aberta.

2.3 ARQUITETURA DE SOFTWARE: REST E JSON

De acordo com Fielding (2000), a arquitetura REST (Representational State Transfer) é um estilo arquitetural para sistemas distribuídos em que os componentes se comunicam sem guardar estado entre requisições (comunicação stateless), o que favorece a escalabilidade e o desacoplamento entre cliente e servidor.

Rodríguez et al. (2016), em uma análise em larga escala, constataram que muitas APIs que se declaram REST não seguem os princípios e as boas práticas do estilo, o que prejudica a manutenção e a reutilização. Palma et al. (2017) propuseram a análise semântica de APIs RESTful para detectar padrões linguísticos e antipadrões na nomeação de recursos.

Bray (2017) especifica o JSON (JavaScript Object Notation) como um formato textual, legível e independente de linguagem para representar estruturas de dados.

2.4 TECNOLOGIAS DE DESENVOLVIMENTO: PYTHON, FASTAPI, POSTGRESQL E FRONT-END WEB

Servidor. Segundo Van Rossum (1991), Python é uma linguagem interpretada, de alto nível e tipagem dinâmica, concebida com ênfase na legibilidade do código. Menezes (2010) mostra como o suporte à orientação a objetos ajuda a modelar domínios com código organizado e extensível. Conforme a documentação de Ramírez (2018), o FastAPI fornece validação de dados, serialização em JSON, documentação interativa no padrão OpenAPI e suporte a operações assíncronas.

Banco de dados. Stonebraker e Kemnitz (1991) descrevem o POSTGRES, origem do PostgreSQL, como um sistema relacional estendido com suporte a tipos de dados complexos e regras. Jung et al. (2015) comparam o desempenho de entrada e saída de dados do MongoDB e do PostgreSQL em ambiente de big data [VERIFICAR esta citação: ver nota 3 no apêndice], e Krocz, Kizun e Skublewska-Paszkowska (2020) analisam o desempenho dos bancos relacionais MySQL, PostgreSQL, MariaDB e H2.

Interface. O HTML5 define os elementos semânticos que estruturam o conteúdo (W3C, 2014), e o CSS3 responde pela estilização e pelo layout adaptativo (W3C, 2018a) [VERIFICAR qual documento do W3C: ver nota 5]. Segundo Flanagan (2013), o JavaScript é a linguagem padrão para a lógica interativa no navegador, com manipulação do DOM e requisições assíncronas sem recarregar a página. Teruel (2014) apresenta de forma prática o uso do HTML5 na construção de interfaces web.

2.5 INTERFACE, USABILIDADE, ACESSIBILIDADE E ORGANIZAÇÃO DA INFORMAÇÃO

Conforme Bader e Hammouri (2016), o design responsivo reúne técnicas que permitem à interface se adaptar a diferentes tamanhos de tela, resoluções e dispositivos, mantendo a experiência de uso consistente. Pathak, Mamloda e Patel (s.d.), ao analisarem sites responsivos, destacam que a navegação intuitiva, a estética visual e a personalização contribuem para a satisfação do usuário.

A usabilidade complementa a responsividade. Cybis, Betiol e Faust (2010) discutem conhecimentos, métodos e aplicações da ergonomia e da usabilidade no projeto de interfaces, e Prates e Barbosa (2003) apresentam conceitos e métodos para avaliar interfaces de usuário.

Quanto à acessibilidade, as Diretrizes de Acessibilidade para Conteúdo Web (WCAG) 2.1 definem critérios para que o conteúdo possa ser percebido, operado e compreendido por pessoas com deficiências visuais, auditivas, motoras e cognitivas (W3C, 2018b). Nagaraju, Chawla e Rana (2019) discutem os desafios práticos de avaliar a acessibilidade de sites segundo as WCAG 2.0 [VERIFICAR esta citação: ver nota 4].

Santarém Segundo e Vidotti (2011) estudam, no contexto de repositórios digitais, o uso de tags associadas à folksonomia assistida para organizar objetos e recuperar informação a partir do conhecimento dos próprios usuários.

2.6 SEGURANÇA E LGPD

A Lei nº 13.709/2018, Lei Geral de Proteção de Dados Pessoais (BRASIL, 2018), regula o tratamento de dados pessoais no país. Entre os princípios da lei estão a necessidade, que limita o tratamento ao mínimo necessário para a realização de suas finalidades, a segurança, que exige medidas técnicas e administrativas aptas a proteger os dados pessoais, e a prevenção, que exige medidas para prevenir danos em virtude do tratamento (BRASIL, 2018, art. 6º, incisos III, VII e VIII). O art. 18 assegura ao titular, entre outros direitos, o acesso aos dados, a correção de dados incompletos, inexatos ou desatualizados e a eliminação de dados tratados com consentimento, e o art. 46 determina que os agentes de tratamento adotem medidas de segurança aptas a proteger os dados pessoais de acessos não autorizados (BRASIL, 2018).

O OWASP (2017) reúne as dez vulnerabilidades mais críticas em aplicações web, entre elas injeção, autenticação quebrada, exposição de dados sensíveis, controle de acesso quebrado, configuração incorreta de segurança, cross-site scripting (XSS), uso de componentes vulneráveis e registro insuficiente de eventos. Nunes et al. (2018) mostram que combinar diferentes ferramentas de análise estática de código amplia a detecção de vulnerabilidades em aplicações web, ainda que nenhuma ferramenta, isoladamente, cubra todos os casos.

3 DELINEAMENTO METODOLÓGICO

O presente trabalho caracterizou-se como uma pesquisa aplicada, pois buscou propor uma solução tecnológica para reduzir o esforço de busca de trabalhos acadêmicos distribuídos em repositórios de acesso aberto independentes. Os objetivos da pesquisa possuíram caráter exploratório e descritivo: foi exploratória ao investigar as interfaces programáticas, os protocolos de interoperabilidade e a viabilidade técnica de integrar CORE, SciELO, OpenAlex e os repositórios institucionais da UESPI, da UFPI e da BDTD, e descritiva ao documentar os requisitos e o comportamento da aplicação desenvolvida.

Sob a perspectiva da abordagem do problema, adotou-se uma análise qualitativa, voltada à compreensão do fluxo de busca do estudante de graduação e à estruturação da arquitetura da aplicação.

Em relação aos procedimentos técnicos, o estudo dividiu-se em três etapas. Inicialmente, foi realizada uma pesquisa bibliográfica para obter o suporte teórico necessário em livros, artigos e documentos técnicos sobre repositórios, interoperabilidade, arquitetura de software, interface e segurança. Em seguida, foram levantadas e testadas as interfaces de consulta de cada repositório, o que permitiu definir os campos de metadados a serem unificados. Por fim, foi feita uma pesquisa tecnológica, na qual foram aplicadas técnicas de modelagem, prototipação e implementação da aplicação por etapas incrementais, com validação a cada etapa.

Para SciELO, BDTD, UFPI e UESPI, previu-se a coleta pelo protocolo OAI-PMH, que não oferece busca por palavra-chave; por isso, os registros colhidos foram armazenados em um índice local no PostgreSQL, sobre o qual a busca foi executada. CORE e OpenAlex foram consultados diretamente por suas APIs no momento da busca. Antes da colheita, a disponibilidade do protocolo foi testada em cada fonte. Como o endereço OAI-PMH da BDTD não respondeu, ela passou a ser consultada no momento da busca pela sua API REST pública. Como nenhum dos repositórios previstos pôde ser colhido, o repositório institucional da Universidade Federal de Pernambuco (UFPE), que respondeu ao protocolo, foi incluído para validar a colheita e a busca no índice local.

O escopo do trabalho foi delimitado a uma aplicação exclusivamente web, acessível por navegador em computadores, tablets e celulares. Ficaram fora desta versão a inclusão de outros repositórios além dos citados, o aplicativo móvel nativo, a recomendação automática de trabalhos, os alertas de novas publicações e a integração direta com gerenciadores de referências, indicados como trabalhos futuros.

4 RESULTADOS E DISCUSSÕES

Este capítulo apresenta a aplicação desenvolvida e o que foi observado na sua verificação. Os números relatados foram obtidos pelo próprio projeto entre 8 e 15 de outubro de 2026, e os totais informados pelas fontes refletem o momento da consulta e mudam com o tempo. Não foi realizada a comparação entre o tempo da busca manual e o da busca na aplicação; por isso, este trabalho não faz afirmações sobre ganho de tempo.

4.1 APRESENTAÇÃO DO ARTEFATO DESENVOLVIDO

A aplicação web reuniu, em uma única tela, o campo de busca, a escolha entre buscar por tema ou pelo nome do autor e a lista unificada de resultados. Cada resultado mostrou título, autores, ano, tipo, resumo quando disponível, a fonte de origem e a ligação para o documento. Acima da lista, a aplicação informou uma estimativa do total de resultados, obtida pela soma dos totais declarados pelas fontes, e quantas fontes responderam. Quando uma fonte falhou ou demorou além do limite, as demais continuaram a ser exibidas e a falha foi indicada na tela. A Figura 1 mostra uma busca por tema, e a Figura 2, uma busca por autor.

Figura 1 – Resultados de uma busca por tema

Fonte: Elaborado pelo Autor (2026).

Figura 2 – Resultados de uma busca por autor

Fonte: Elaborado pelo Autor (2026).

Os resultados puderam ser filtrados por intervalo de anos e por tipo de publicação (artigo, tese ou dissertação, preprint, livro e outros), ordenados por relevância ou por ano e paginados. O painel de filtros também indicou as fontes indisponíveis, que não podem ser marcadas, como mostra a Figura 3. A busca foi permitida sem cadastro; o cadastro deu acesso aos favoritos, ao histórico de buscas e à área da conta.

Figura 3 – Painel de filtros com intervalo de anos e tipo aplicados

Fonte: Elaborado pelo Autor (2026).

As figuras deste capítulo foram capturadas na aplicação em funcionamento, com dados reais das fontes, em 15 de outubro de 2026. A conta usada nas telas que exigem cadastro foi uma conta de teste, com nome e e-mail fictícios.

4.2 INTEGRAÇÃO, NORMALIZAÇÃO E COLETA DE DADOS

A integração seguiu a diferença entre fontes que oferecem busca por palavra-chave em uma API e fontes que oferecem apenas a coleta de metadados em lote. CORE, OpenAlex e BDTD foram consultados no momento da busca, cada um por um conector próprio, em paralelo e com tempo limite individual, de modo que a falha de uma fonte não impediu a resposta das demais. Para os repositórios institucionais, adotou-se o protocolo OAI-PMH, que, conforme Lagoze et al. (2002), normatiza a coleta de metadados entre provedores de dados e provedores de serviços. Como o protocolo não oferece busca por palavra-chave, os registros foram colhidos por uma ferramenta de linha de comando, de forma incremental e com pausa entre requisições, e gravados em um índice local no PostgreSQL, no qual a busca foi feita.

A verificação de cada fonte com respostas reais, resumida no Quadro 1, mostrou que a disponibilidade dos protocolos não correspondeu ao que se previa. Almeida e Dias (2023) registram que os dados da BDTD são coletados via OAI-PMH; no entanto, o endereço OAI-PMH da BDTD respondeu com erro 404 nos testes deste trabalho. A BDTD oferece, porém, uma API REST pública, que respondeu à busca por tema e por autor, ao filtro de anos, à ordenação por ano e à paginação, e a integração foi feita por ela. Para o SciELO, nenhum endereço OAI-PMH testado respondeu no formato Extensible Markup Language (XML) exigido pelo protocolo. Os repositórios da UFPI e da UESPI responderam ao protocolo, mas com o índice vazio, e apresentaram cadeia de certificados Transport Layer Security (TLS) incompleta, o que impediu a conexão segura. No caso da UESPI, o repositório existe por determinação da Resolução CEPEX nº 034/2024 (UESPI, 2024), que prevê o depósito dos trabalhos pelo SIGAA, mas os registros não estavam acessíveis pelo protocolo no momento dos testes. A verificação de certificado não foi desativada, por comprometer a segurança da coleta, e a solução depende dos administradores dos repositórios. Essas quatro fontes permaneceram descritas na configuração da aplicação, desligadas.

Quadro 1 – Situação de cada fonte nos testes de 8 a 15 de outubro de 2026

| Fonte | Forma de integração | Resultado dos testes |
|---|---|---|
| CORE | API, consultada no momento da busca | Integrada; respostas reais validadas |
| SciELO | OAI-PMH previsto | Nenhum endereço OAI-PMH respondeu em XML; não integrada |
| OpenAlex | API, consultada no momento da busca | Integrada; 11 casos de busca e filtro validados |
| BDTD | OAI-PMH previsto; API REST adotada | OAI-PMH respondeu 404; integrada pela API REST, 12 casos validados |
| UFPI | OAI-PMH | Índice vazio e cadeia de certificados TLS incompleta; não integrada |
| UESPI | OAI-PMH | Índice vazio e cadeia de certificados TLS incompleta; não integrada |
| UFPE | OAI-PMH, índice local | Incluída para validar a colheita; 12.366 registros colhidos |

Fonte: Elaborado pelo Autor (2026).

A comparação das respostas reais com a documentação das fontes também levou a ajustes nos conectores. No CORE, os tipos de documento usados pela fonte diferiam dos esperados, a busca por autor só foi aceita em uma forma específica de consulta, o texto completo dos trabalhos foi excluído das respostas, que ficavam volumosas, e o tempo limite foi ampliado, porque a fonte respondeu de forma lenta e recusou chamadas em sequência rápida. Na BDTD, os nomes dos autores vieram, em alguns registros, acompanhados da sigla da instituição entre colchetes, que foi retirada.

Para unificar as fontes, os campos de cada uma foram mapeados para um modelo único, com título, autores, ano, tipo, idioma, resumo, identificador digital, endereço do trabalho e endereço do arquivo, seguindo a interoperabilidade no nível do esquema discutida por Chan e Zeng (2006). Os valores de tipo de cada fonte foram traduzidos para um conjunto comum, e, no nível do registro tratado por Zeng e Chan (2006), os trabalhos repetidos entre fontes foram consolidados em um só, pelo identificador digital de objeto (Digital Object Identifier, DOI) e, na falta dele, pelo título, pelo ano e pelo sobrenome do primeiro autor.

A busca por autor exigiu tratamento diferente do da busca por tema. No índice local, os nomes foram indexados sem a redução das palavras ao radical, usada na busca por tema, porque o radical confundiria nomes próximos; na consulta às fontes externas, foi usado o campo de autor de cada uma. A busca apenas pelo sobrenome trouxe homônimos, o que é uma limitação da busca por nome sem identificador de autor.

A raspagem de dados, que, de acordo com Vargiu e Urru (2012), consiste no uso de algoritmos para extrair informações públicas de páginas HTML, foi usada apenas para completar o resumo de registros que chegaram sem ele, e não para suprir fonte. Ela fica desligada por padrão no código e foi ligada na configuração de uso deste projeto. A raspagem atuou depois da busca, em no máximo cinco registros por consulta, respeitou o arquivo robots.txt de cada domínio, manteve pausa de dois segundos entre requisições ao mesmo domínio, identificou-se com o nome da aplicação e um contato e extraiu apenas o resumo, a partir de marcações padronizadas da página. Nas três tentativas de medição realizadas, nenhum resumo foi completado, e a aplicação passou a registrar o motivo de cada recusa. O resultado mostrou que, nas condições testadas, a raspagem teve papel apenas eventual.

4.3 ARQUITETURA E TECNOLOGIAS

O servidor foi escrito em Python com o FastAPI, que, conforme a documentação de Ramírez (2018), fornece validação de dados, serialização em JSON, documentação no padrão OpenAPI e suporte a operações assíncronas; esta última característica permitiu consultar as fontes em paralelo. Os dados foram guardados no PostgreSQL, cuja origem Stonebraker e Kemnitz (1991) descrevem como um sistema relacional estendido. O PostgreSQL foi escolhido pelos recursos de busca textual com dicionário em português e remoção de acentos, usados no índice local; a comparação de desempenho entre bancos relacionais feita por Krocz, Kizun e Skublewska-Paszkowska (2020) não foi reproduzida neste trabalho. A interface foi escrita em HTML5, CSS3 e JavaScript, sem etapa de compilação, e os dados trocados entre a interface e o servidor seguiram o formato JSON especificado por Bray (2017).

A API foi construída no estilo REST descrito por Fielding (2000), sem guardar estado entre requisições: a identificação do usuário foi enviada em cada chamada, por meio de um token. Como Rodríguez et al. (2016) mostram que muitas APIs que se declaram REST não seguem os princípios do estilo, e Palma et al. (2017) tratam dos antipadrões na nomeação de recursos, cada rota da API foi avaliada pelo autor quanto a quatro critérios: se o verbo HTTP corresponde à operação, se o caminho nomeia um recurso por um substantivo no plural, se o código de status é o adequado e se a resposta é sem estado. O Quadro 2 apresenta o resultado.

Quadro 2 – Autoavaliação das rotas da API

| Rota | Verbo | Nome no plural | Código de status | Sem estado |
|---|---|---|---|---|
| GET /health | Atende | N/A | Parcial | Atende |
| POST /auth/register | Atende | Não atende | Atende | Atende |
| POST /auth/login | Atende | Não atende | Parcial | Atende |
| GET /auth/me | Atende | Parcial | Atende | Atende |
| GET /search | Atende | Parcial | Atende | Atende |
| GET /sources | Atende | Atende | Atende | Atende |
| GET /favorites/export | Atende | Não atende | Atende | Atende |
| POST /export | Parcial | Não atende | Parcial | Atende |
| POST /favorites | Atende | Atende | Atende | Atende |
| GET /favorites | Atende | Atende | Atende | Atende |
| PATCH /favorites/{favorite_id} | Atende | Atende | Atende | Atende |
| DELETE /favorites/{favorite_id} | Atende | Atende | Atende | Atende |
| GET /history | Atende | Parcial | Atende | Atende |
| DELETE /history | Atende | Parcial | Atende | Atende |
| DELETE /history/{history_id} | Atende | Parcial | Atende | Atende |
| GET /me | Atende | Parcial | Atende | Atende |
| PATCH /me | Atende | Parcial | Parcial | Atende |
| DELETE /me | Parcial | Parcial | Parcial | Atende |
| POST /me/password | Parcial | Parcial | Atende | Atende |
| GET /me/data-export | Atende | Parcial | Atende | Atende |
| POST /me/consent | Atende | Parcial | Atende | Atende |
| GET /privacy | Atende | Parcial | Atende | Atende |

Fonte: Elaborado pelo Autor (2026).

Todas as rotas atenderam ao critério de ausência de estado. O principal desvio esteve na nomeação, o mesmo tipo de antipadrão discutido por Palma et al. (2017): as rotas de cadastro, de entrada e de exportação usam verbos no caminho (register, login e export) em vez de substantivos. Esses desvios foram mantidos e documentados, com a alternativa que seguiria a convenção.

4.4 INTERFACE, USABILIDADE E ACESSIBILIDADE

O layout foi construído primeiro para telas pequenas e ampliado para telas maiores, segundo as técnicas de design responsivo descritas por Bader e Hammouri (2016): tamanhos relativos, menu recolhível em telas estreitas, alvos de toque de pelo menos 44 por 44 pixels e ausência de rolagem horizontal em 320 pixels de largura e com o texto ampliado a 200%. A Figura 4 mostra a tela de resultados em largura de celular.

Figura 4 – Resultados em largura de celular

Fonte: Elaborado pelo Autor (2026).

Quanto à acessibilidade, a interface foi desenvolvida com base nas WCAG 2.1 (W3C, 2018b): idioma da página declarado, estrutura de títulos e regiões, ligação para pular ao conteúdo, foco visível em todos os elementos, mensagens de estado anunciadas a leitores de tela e cor nunca usada como único sinal. Os pares de cor de texto foram calculados por programa, e todos atingiram contraste de pelo menos 4,5:1. A verificação automática com a ferramenta axe-core percorreu 17 telas e estados em duas larguras, em 34 execuções, e não encontrou violações. Como a verificação automática cobre apenas parte dos critérios e não houve teste com leitor de tela nem com pessoas com deficiência, a interface atende aos critérios verificados, e não se afirma conformidade plena com as WCAG 2.1.

A usabilidade foi avaliada por inspeção, pelo método da avaliação heurística apresentado por Prates e Barbosa (2003) e discutido por Cybis, Betiol e Faust (2010), aplicando-se a cada tela as dez heurísticas de usabilidade de Nielsen (1994 apud PRATES; BARBOSA, 2003). A inspeção foi feita por um único avaliador, com o apoio da ferramenta de inteligência artificial usada no desenvolvimento, sem a participação de usuários. Foram registrados 13 problemas: dois de gravidade 3, três de gravidade 2 e oito de gravidade 1. Os dois mais graves foram a perda da sessão ao voltar à busca depois de entrar, que devolvia o usuário à tela de entrada, e a ausência do contato do responsável na política de privacidade; entre os de gravidade 2 esteve a falta de aviso de que não há recuperação de senha. Os problemas de gravidade 3 e 2 foram corrigidos ou atenuados, e os de gravidade 1 foram aceitos com justificativa. A recuperação de senha não foi implementada, porque exigiria o envio de e-mails.

4.5 FAVORITOS E EXPORTAÇÃO DE RESULTADOS

O usuário cadastrado pôde salvar resultados nos favoritos, sem duplicar um trabalho já salvo, registrar em cada favorito uma anotação em texto livre e pesquisar dentro dos próprios favoritos, como mostra a Figura 5. Santarém Segundo e Vidotti (2011) estudam o uso de tags associadas à folksonomia assistida para organizar objetos e recuperar informação; essa organização por tags não foi implementada nesta versão, que se limitou à anotação livre. O histórico guardou as 200 buscas mais recentes de cada usuário, com o tipo de busca e os filtros, e permitiu repetir uma busca.

Figura 5 – Favoritos com anotação

Fonte: Elaborado pelo Autor (2026).

A exportação gerou arquivos nos formatos BibTeX e RIS, lidos por gerenciadores de referências, além de JSON e CSV, a partir dos resultados selecionados, até 100 por vez, ou de todos os favoritos, como mostra a Figura 6. A escolha dos formatos foi decisão de projeto, voltada à reutilização das referências pelo estudante de graduação. O arquivo CSV foi protegido contra a execução de fórmulas ao ser aberto em planilhas. A sincronização direta com gerenciadores de referências não foi implementada.

Figura 6 – Seleção de resultados para exportação em BibTeX

Fonte: Elaborado pelo Autor (2026).

4.6 SEGURANÇA E PRIVACIDADE (LGPD)

A Lei nº 13.709/2018, Lei Geral de Proteção de Dados Pessoais (LGPD), limita o tratamento ao mínimo necessário para as suas finalidades (BRASIL, 2018, art. 6º, inciso III), e a aplicação guardou apenas nome, e-mail, a senha na forma de resumo criptográfico (Argon2id), a data e a versão do aceite da política de privacidade, os favoritos com anotações, o histórico de buscas e os eventos de segurança, nos quais o endereço de rede foi guardado apenas de forma irreversível. Não foram coletados telefone, CPF, data de nascimento, cookies de rastreamento nem dados de análise de uso. A política de privacidade, aceita no cadastro, informou que o texto da busca é enviado às fontes consultadas no momento da busca. Os direitos do art. 18 foram atendidos por rotas da API: acesso aos dados, cópia em arquivo JSON, correção de nome, e-mail e senha, eliminação do histórico, dos favoritos e da própria conta, e novo aceite quando a versão da política muda. Em atenção ao art. 46, que exige medidas de segurança contra acessos não autorizados, foram aplicados os controles descritos a seguir.

Cada um dos dez riscos do OWASP (2017) foi relacionado ao ponto da aplicação em que poderia ocorrer, ao controle implementado e ao teste que o confere. Entre os controles estiveram consultas ao banco com parâmetros (injeção), resumo criptográfico das senhas, mensagem única de erro no login e limite de tentativas (autenticação quebrada), leitura de XML com bloqueio de entidades externas, filtro de todas as consultas pelo usuário dono do dado (controle de acesso quebrado), cabeçalhos de segurança e montagem da página sem inserir HTML vindo de fora (XSS) e registro dos eventos de segurança (registro insuficiente de eventos).

Nunes et al. (2018) mostram que combinar ferramentas de análise estática amplia a detecção de vulnerabilidades, e por isso foram usadas quatro: bandit, semgrep, pip-audit e as regras de segurança do ruff. Na execução final, em 14 de outubro de 2026, bandit, semgrep e pip-audit não apontaram achados, e as regras do ruff apontaram três falsos positivos, justificados no código. Durante o trabalho, o próprio programa de análise reaproveitou por engano um resultado antigo do semgrep; o defeito foi corrigido e a análise refeita. A ausência de achados não prova ausência de falhas: a análise foi estática e não houve teste de intrusão.

O conjunto da aplicação foi verificado por testes automatizados. Em 15 de outubro de 2026, a suíte completa teve 1.251 testes aprovados e 2 ignorados, com cobertura de 98,07% das linhas do código da aplicação (3.264 linhas, 63 não cobertas).

5 CONCLUSÕES

O objetivo geral deste trabalho foi desenvolver uma aplicação web que centralizasse a busca por trabalhos acadêmicos em CORE, SciELO, OpenAlex e nos repositórios da UESPI, da UFPI e da BDTD. O objetivo foi cumprido em parte. A aplicação foi construída e entregou busca unificada por tema ou por autor, filtros por ano e tipo, unificação de resultados repetidos, favoritos com anotação, histórico, exportação em BibTeX, RIS, JSON e CSV e uma API pública documentada, e foi verificada por testes automatizados, análise estática e verificação automática de acessibilidade.

Das seis fontes previstas, três foram integradas e validadas com respostas reais: CORE, OpenAlex e BDTD, esta pela API REST, porque o seu endereço OAI-PMH não respondeu. SciELO, UFPI e UESPI não puderam ser integrados por razões externas à aplicação: no SciELO, nenhum endereço OAI-PMH respondeu; na UFPI e na UESPI, o índice OAI-PMH estava vazio e a cadeia de certificados estava incompleta. A colheita por OAI-PMH e a busca no índice local foram comprovadas com o repositório da UFPE, incluído para essa validação. Assim, a busca nos repositórios da UESPI e da UFPI, parte central da motivação do trabalho, não foi alcançada nesta versão e depende da correção desses repositórios pelos seus administradores.

Também não foi medido o tempo da busca na aplicação em comparação com a busca manual, de modo que este trabalho não sustenta afirmações de ganho de tempo. A avaliação de usabilidade foi feita por inspeção, sem usuários, e a de acessibilidade foi automática, sem leitor de tela, o que limita as conclusões sobre o uso real. A raspagem de resumos não completou nenhum resumo nas tentativas realizadas. Permaneceram ainda os desvios de nomeação de três rotas da API e a ausência de recuperação de senha.

Como perspectivas para a continuidade do projeto, sugerem-se as seguintes evoluções:

- Aplicativo móvel nativo: desenvolver versões para Android e iOS a partir da API pública já disponível.

- Recomendação de trabalhos: sugerir publicações relacionadas com base no histórico de buscas e nos favoritos do usuário.

- Novos repositórios: incluir repositórios de outras universidades além das fontes já integradas (CORE, SciELO, OpenAlex, BDTD, UFPI e UESPI).

- Alertas: avisar o usuário, por e-mail ou notificação, quando houver novas publicações sobre um tema salvo.

- Gerenciadores de referências: sincronizar os favoritos diretamente com ferramentas como Zotero e Mendeley.

- Outros idiomas e autenticação em dois fatores: traduzir a interface e reforçar o acesso às contas.

REFERÊNCIAS

ALMEIDA, L. S.; DIAS, T. M. R. Análise dos mecanismos de busca de repositórios institucionais de acesso aberto. RDBCI: Revista Digital de Biblioteconomia e Ciência da Informação, Campinas, v. 21, 2023. DOI 10.20396/rdbci.v20i00.8672274. Disponível em: https://www.scielo.br/j/rdbci/a/XbdZdMMTGFkSdxhL858PdCt/. Acesso em: 7 out. 2026. [conferir: o volume aparece como 21 e o DOI como v20]

BADER, W. I.; HAMMOURI, A. I. Responsive web design techniques. International Journal of Computer Applications, v. 150, n. 2, p. 18-27, set. 2016. DOI 10.5120/ijca2016911463. Disponível em: https://www.ijcaonline.org/archives/volume150/number2/26066-2016911463/. Acesso em: 8 out. 2026.

BRASIL. Lei nº 13.709, de 14 de agosto de 2018. Lei Geral de Proteção de Dados Pessoais (LGPD). Diário Oficial da União: seção 1, Brasília, DF, 15 ago. 2018. Disponível em: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm. Acesso em: [inserir a data em que você abriu].

BRAY, T. (ed.). The JavaScript Object Notation (JSON) data interchange format. RFC 8259. [S. l.]: Internet Engineering Task Force, dez. 2017. Disponível em: https://www.rfc-editor.org/rfc/rfc8259. Acesso em: [inserir a data].

CHAN, L. M.; ZENG, M. L. Metadata interoperability and standardization: a study of methodology. Part I: achieving interoperability at schema level. D-Lib Magazine, Washington, DC, v. 12, n. 6, p. 1-15, 2006. Disponível em: https://dlib.org/dlib/june06/chan/06chan.html. Acesso em: 29 set. 2026.

CYBIS, W.; BETIOL, A. H.; FAUST, R. Ergonomia e usabilidade: conhecimentos, métodos e aplicações. [inserir edição]. São Paulo: Novatec, 2010. [conferir edição, editora e subtítulo no exemplar que você usou]

FIELDING, R. T. Architectural styles and the design of network-based software architectures. 2000. Tese (Doutorado em Ciência da Computação) – University of California, Irvine, 2000. Disponível em: https://www.ics.uci.edu/~fielding/pubs/dissertation/top.htm. Acesso em: 29 set. 2026.

FLANAGAN, D. JavaScript: o guia definitivo. [inserir edição]. Porto Alegre: Bookman, 2013. [conferir título, edição, tradutor e editora]

IBICT. Manifesto brasileiro de apoio ao acesso livre à informação científica. Brasília, DF: IBICT, [2005]. Disponível em: https://www.icict.fiocruz.br/sites/www.icict.fiocruz.br/files/Manifesto%20sobre%20o%20acesso%20livre%20a%20informacao%20cientifica.pdf. Acesso em: [inserir a data]. [confirmar o ano e o órgão emissor no site do IBICT]

JUNG, [prenome] et al. [título]. [periódico ou anais], [local, volume, número, páginas], 2015. [FONTE NÃO LOCALIZADA: ver nota 3 do apêndice]

KNOTH, P.; ZDRAHAL, Z. CORE: three access levels to underpin open access. D-Lib Magazine, Washington, DC, v. 18, n. 11/12, nov./dez. 2012. Disponível em: https://dlib.org/dlib/november12/knoth/11knoth.html. Acesso em: 7 out. 2026.

KROCZ, K.; KIZUN, O.; SKUBLEWSKA-PASZKOWSKA, M. Perfomance analysis of relational databases MySQL, PostgreSQL, MariaDB and H2. Journal of Computer Sciences Institute, v. 14, p. 1-7, 2020. DOI 10.35784/jcsi.1565. Disponível em: https://ph.pollub.pl/index.php/jcsi/article/view/1565. Acesso em: 8 out. 2026. [a palavra “Perfomance” está grafada assim no título original]

LAGOZE, C.; VAN DE SOMPEL, H.; NELSON, M. L.; WARNER, S. The Open Archives Initiative protocol for metadata harvesting: protocol version 2.0 of 2002-06-14. Ithaca, NY: Cornell University, 2002. Disponível em: http://www.openarchives.org/OAI/2.0/openarchivesprotocol.htm. Acesso em: 29 set. 2026.

LYNCH, C. A. Institutional repositories: essential infrastructure for scholarship in the digital age. ARL Bimonthly Report, Washington, DC, n. 226, 2003. Disponível em: https://www.openarchives.org/news/oaiv2press020614.html. Acesso em: 29 set. 2026. [o endereço da sua lista aponta para outro documento; confira o link do artigo]

MENEZES, N. N. C. [título]. [edição]. São Paulo: Novatec, 2010. [COMPLETAR: obra sobre orientação a objetos citada na seção 2.4]

NAGARAJU, [prenome]; CHAWLA, [prenome]; RANA, [prenome]. [título]. [periódico], [local, volume, número, páginas], 2019. [FONTE NÃO LOCALIZADA: ver nota 4 do apêndice]

NUNES, P.; MEDEIROS, I.; FONSECA, J.; NEVES, N. F.; CORREIA, M.; VIEIRA, M. Benchmarking static analysis tools for web security. IEEE Transactions on Reliability, v. 67, n. 3, p. 1159-1175, set. 2018. [confirmar se este é o artigo que você leu; ver nota 6]

OWASP. OWASP Top 10 – 2017: the ten most critical web application security risks. [S. l.]: OWASP Foundation, 2017. Disponível em: [inserir o endereço]. Acesso em: [inserir a data]. [decidir entre a edição de 2017 e a de 2021 e usar a mesma em todo o trabalho]

PACKER, A. L. [título exato]. In: ICSU PRESS WORKSHOP, 1998, Oxford. Oxford: Keble College, 1998. Disponível em: https://wp.scielo.org/wp-content/uploads/PACKER-A.L.-SciELO-Biblioteca-Eletr%C3%B4nica-Cient%C3%ADfica-Online.pdf. Acesso em: 7 out. 2026. [conferir o título exato no PDF]

PALMA, F.; GONZALEZ-HUERTA, J.; FOUNI, M.; MOHA, N.; TREMBLAY, G.; GUÉHÉNEUC, Y.-G. Semantic analysis of RESTful APIs for the detection of linguistic patterns and antipatterns. International Journal of Cooperative Information Systems, v. 26, n. 2, 2017. DOI 10.1142/S0218843017420011. [a página consultada informa 37 páginas, sem intervalo; confira o intervalo de páginas]

PATHAK, B.; MAMLODA, S.; PATEL, M. Responsive e-commerce website. Vadodara: Parul University, [s. d.]. [COMPLETAR ano, periódico, volume, páginas e DOI; o arquivo que você anexou não traz esses dados]

PRATES, R. O.; BARBOSA, S. D. J. Avaliação de interfaces de usuário: conceitos e métodos. In: [nome do evento e edição], 2003, [local]. Anais. [local]: SBC, 2003. Cap. 6. [intervalo de páginas]. [confirmei autores, título e o número do capítulo; o evento, o local e as páginas não aparecem no PDF que abri]

PRIEM, J.; PIWOWAR, H.; ORR, R. OpenAlex: a fully-open index of scholarly works, authors, venues, institutions, and concepts. In: INTERNATIONAL CONFERENCE ON SCIENCE, TECHNOLOGY AND INNOVATION INDICATORS (STI), 26., 2022. Anais. [S. l.: s. n.], 2022. arXiv:2205.01833. Disponível em: https://arxiv.org/abs/2205.01833. Acesso em: 7 out. 2026.

RAMÍREZ, S. FastAPI: documentação oficial. 2018. Disponível em: https://fastapi.tiangolo.com/. Acesso em: [inserir a data]. [conferir a forma de citar documentação de software e o ano de início do projeto]

RODRÍGUEZ, C. et al. REST APIs: a large-scale analysis of compliance with principles and best practices. In: INTERNATIONAL CONFERENCE ON WEB ENGINEERING (ICWE), 16., 2016, Lugano. Proceedings. Cham: Springer, 2016. p. 21-39. (Lecture Notes in Computer Science). DOI 10.1007/978-3-319-38791-8_2.

SANTARÉM SEGUNDO, J. E.; VIDOTTI, S. A. B. G. Rede de tags para recuperação da informação no contexto da representação iterativa. InCID: Revista de Ciência da Informação e Documentação, Ribeirão Preto, v. 2, n. 1, p. 86-109, 2011. Disponível em: https://www.revistas.usp.br/incid/article/view/42336. Acesso em: 29 set. 2026.

STONEBRAKER, M.; KEMNITZ, G. The POSTGRES next generation database management system. Communications of the ACM, Nova York, v. 34, n. 10, p. 78-92, 1991. Disponível em: https://vldb.org/dblp/db/journals/cacm/StonebrakerK91.html. Acesso em: 29 set. 2026.

SUBER, P. Open access. 1. ed. Cambridge, MA: MIT Press, 2012. Disponível em: https://mitpress.mit.edu/9780262517638. Acesso em: 29 set. 2026.

TERUEL, E. C. HTML5: [subtítulo]. [edição]. São Paulo: Érica, 2014. [conferir autor, título, subtítulo, edição e editora]

UNIVERSIDADE ESTADUAL DO PIAUÍ. Conselho de Ensino, Pesquisa e Extensão. Resolução CEPEX nº 034/2024, de 21 de agosto de 2024. Institui o repositório institucional de trabalhos acadêmicos. Teresina: UESPI, 2024. Disponível em: https://uespi.br/wp-content/uploads/2024/09/RESOLUCAO_CEPEX___Instituir_o_repositorio_institucional_de_Trabalhos_Academicos.pdf. Acesso em: 7 out. 2026.

VAN ROSSUM, G. [título]. [local]: [editora], 1991. [COMPLETAR: obra ou documento citado na seção 2.4. Se a intenção era citar a criação da linguagem, considere a documentação oficial do Python ou um texto histórico do autor]

VARGIU, E.; URRU, M. Exploiting web scraping in a collaborative filtering-based approach to web advertising. Artificial Intelligence Research, Ontario, v. 2, n. 1, p. 44-54, 2012. DOI 10.5430/air.v2n1p44. Disponível em: https://www.sciedu.ca/journal/index.php/air/article/view/1390/0. Acesso em: 29 set. 2026.

W3C. HTML5: a vocabulary and associated APIs for HTML and XHTML. W3C Recommendation, 28 out. 2014. Disponível em: https://www.w3.org/TR/html5/. Acesso em: [inserir a data]. [conferir a versão da recomendação que você consultou]

W3C. [título do documento de CSS consultado]. W3C, 2018a. Disponível em: [inserir o endereço]. Acesso em: [inserir a data]. [COMPLETAR: ver nota 5 do apêndice]

W3C. Web Content Accessibility Guidelines (WCAG) 2.1. W3C Recommendation, 5 jun. 2018b. Disponível em: https://www.w3.org/TR/WCAG21/. Acesso em: [inserir a data].

ZENG, M. L.; CHAN, L. M. Metadata interoperability and standardization: a study of methodology. Part II: achieving interoperability at record and repository levels. D-Lib Magazine, Washington, DC, v. 12, n. 6, p. 1-20, 2006. Disponível em: https://dlib.org/dlib/june06/zeng/06zeng.html. Acesso em: 29 set. 2026.

APÊNDICE — NOTAS PARA O AUTOR (APAGAR ANTES DE ENTREGAR)

Todo o texto em vermelho e itálico deste arquivo é aviso meu, inclusive os roteiros das seções 4 e 5 e os trechos entre colchetes nas referências. Apague tudo antes de entregar.

1. Regras seguidas. A Introdução não tem nenhuma citação. O Referencial tem apenas citações diretas e indiretas, sem frases de autoria sua. O Delineamento está no passado e sem citações. A sigla é UESPI. As seções 4 e 5 estão em esqueleto porque dependem do sistema pronto.

2. Ordem dos autores de Bader e Hammouri. A sua citação dizia “Hammouri e Bader (2016)”. Na página do artigo, a ordem dos autores é Waseem I. Bader e Abdelaziz I. Hammouri. Corrigi para “Bader e Hammouri (2016)” nas seções 2.5 e 4.4. Confira na página do periódico.

3. Jung et al. (2015). Não localizei este trabalho. O artigo mais próximo que encontrei é coreano, de 2017, e compara MongoDB com MySQL, não com PostgreSQL. Ou seja, a frase da seção 2.4 pode estar atribuída à fonte errada. Localize o trabalho que você leu e corrija a frase e a referência, ou retire a citação.

4. Nagaraju, Chawla e Rana (2019). Não localizei nenhum trabalho com esses três autores sobre avaliação de acessibilidade. O artigo que trata exatamente do que a frase diz é “Web Accessibility Challenges”, de Hayfa Y. Abuaddous, Mohd Zalisham Jali e Nurlida Basir, publicado no International Journal of Advanced Computer Science and Applications, v. 7, n. 10, p. 172-181, 2016 (DOI 10.14569/IJACSA.2016.071023). Verifique qual é a fonte correta. Se adotar o artigo de Abuaddous, troque o nome na seção 2.5, na 4.4 e na lista de referências.

5. As duas entradas do W3C de 2018. O texto cita o W3C de 2018 duas vezes, uma para CSS3 e outra para as WCAG 2.1. Pela ABNT, duas obras do mesmo autor no mesmo ano precisam de letras: usei 2018a para o documento de CSS e 2018b para as WCAG 2.1. Falta identificar qual documento de CSS você consultou, porque “CSS3” não é um documento único, e sim um conjunto de módulos.

6. Nunes et al. (2018). A frase da seção 2.6 corresponde ao artigo “Benchmarking Static Analysis Tools for Web Security”, de Paulo Nunes e outros, na IEEE Transactions on Reliability, v. 67, n. 3, p. 1159-1175, 2018. Confirme se é esse o artigo que você leu, porque o grupo publicou vários trabalhos próximos.

7. Fontes que não reabri. O que o texto diz de Cybis, Prates e Barbosa, Menezes, Flanagan, Teruel, Van Rossum, Ramírez e Pathak veio do seu texto original ou do título da obra. Leia cada uma e confirme se a frase corresponde ao conteúdo.

8. Vargiu e Urru (2012). O artigo trata de raspagem aplicada à publicidade. Serve para definir a técnica, mas pergunte ao seu orientador se basta.

9. Santarém Segundo e Vidotti (2011). Sustenta apenas a organização por tags. Nenhuma fonte sustenta a exportação de referências; se for citar algo na seção 4.5, procure uma fonte própria.

10. Repositórios da BDTD, da UFPI e da UESPI. Da BDTD eu só tenho o artigo de Almeida e Dias (2023), não uma página oficial de apresentação. Da UFPI não há fonte no referencial. Os endereços OAI-PMH das quatro fontes colhidas (SciELO, BDTD, UFPI e UESPI) não foram confirmados, e o repositório da UESPI pode não expor o protocolo. Se não expuser, isso vira uma limitação a declarar na seção 4.2 e nas Conclusões.

11. Medição. Se você não fizer a medição comparando a busca manual com a da aplicação, retire do trabalho qualquer afirmação de redução de tempo.

12. Formatação. Usei Times New Roman 12, margens de 3 cm em cima e à esquerda e 2 cm embaixo e à direita, espaçamento 1,5 no corpo do texto, recuo de 1,25 cm na primeira linha e referências alinhadas à esquerda com espaçamento simples. Ajuste ao manual de normalização da UESPI, que tem prioridade sobre o que eu fiz aqui.

14. Citar Cybis e Prates e Barbosa com honestidade. Essas duas obras tratam de métodos de avaliação de interfaces. Se você não aplicar nenhum método de avaliação, não dá para citá-las na seção 4.4 como se tivesse avaliado. Acrescentei a OS-036 ao arquivo de ordens de serviço: ela é uma avaliação heurística que você mesmo faz, e é ela que sustenta a citação. Se você usar as heurísticas de Nielsen, cite Nielsen, e não essas duas obras.

15. Tags x anotação. A seção 2.5 cita organização por tags, mas o sistema especificado guarda uma anotação em texto livre, não tags. Na seção 4.5, descreva o que o sistema faz e diga que a organização por tags não foi implementada nesta versão.

16. Autoavaliação da API, para Rodríguez e Palma. Os dois tratam de APIs que se dizem REST mas não seguem os princípios, e de antipadrões na nomeação de recursos. Para a seção 4.3 ficar sustentada, a OS-034 agora pede uma autoavaliação da sua própria API, rota por rota. Use essa tabela no texto.

17. Raspagem. Ajustei a Introdução: a raspagem não serve para suprir uma fonte sem interface programática, porque todas as seis fontes têm API ou OAI-PMH. Ela serve para completar campos ausentes, como o resumo, e fica desligada por padrão. Se você não ligar a raspagem, diga na seção 4.2 que ela foi especificada e não foi usada.

18. Favoritos, login e exportação nas capturas. Se você fizer hoje apenas a Fatia 1 do arquivo de ordens de serviço (busca, resultados e filtros), não existem telas de favoritos, login, conta nem exportação. Não tire captura de botão desabilitado como se funcionasse, e não descreva essas funções na seção 4 antes de implementá-las.

13. O que ainda falta no arquivo. Capa, folha de rosto, folha de aprovação, dedicatória, agradecimentos, resumo e abstract com palavras-chave, listas de figuras e de abreviaturas, sumário e numeração de páginas. Esses elementos seguem o modelo da UESPI e normalmente são montados no próprio editor.
