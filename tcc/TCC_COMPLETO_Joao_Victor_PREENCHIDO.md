1 INTRODUÇÃO

A elaboração de um Trabalho de Conclusão de Curso (TCC) exige que o estudante de graduação da Universidade Estadual do Piauí (UESPI) realize, logo nas etapas iniciais, um levantamento bibliográfico que sustente o tema escolhido. Esse levantamento depende de fontes abertas e confiáveis, e a produção científica disponível em acesso aberto está distribuída em plataformas independentes, cada uma com sua própria interface, lógica de busca e estrutura de dados.

Os repositórios institucionais e o movimento de acesso aberto ampliaram a disponibilidade de literatura científica gratuita. Apesar desse avanço, o estudante que precisa consultar CORE, SciELO, OpenAlex e os repositórios institucionais da UESPI, da UFPI e da Biblioteca Digital Brasileira de Teses e Dissertações (BDTD) repete a mesma pergunta em vários sistemas, compara resultados duplicados e organiza manualmente as referências encontradas. Esse trabalho repetitivo consome tempo que poderia ser dedicado à leitura e à análise dos textos.

Diante dessa situação, a questão que orienta esta pesquisa é: como uma aplicação web pode contribuir para que estudantes de graduação da UESPI localizem, em uma única consulta, trabalhos acadêmicos disponíveis em múltiplos repositórios de acesso aberto?

O objeto de pesquisa deste trabalho é o projeto, a modelagem e o desenvolvimento de uma aplicação web que centraliza a busca em CORE, SciELO, OpenAlex e nos repositórios institucionais da UESPI, da UFPI e da BDTD. A integração utiliza, prioritariamente, interfaces programáticas e o protocolo OAI-PMH, e recorre à raspagem de dados (web scraping) apenas como complemento, para completar campos que as fontes não trazem em seus metadados, como o resumo. Das fontes previstas, a integração foi validada com respostas reais para o OpenAlex, o CORE e, por OAI-PMH, o repositório da Universidade Federal de Pernambuco, incluído durante o desenvolvimento; as demais permaneceram configuradas, mas não puderam ser colhidas, como se detalha no capítulo 4. [DECIDIR: ver aviso 1] A aplicação oferece busca unificada por tema ou por autor, filtros por ano e tipo de publicação, favoritos, exportação de resultados em formatos usados por gerenciadores de referências e uma API pública.

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

Como os repositórios institucionais expõem seus metadados pelo protocolo OAI-PMH, que não oferece busca por palavra-chave, os registros colhidos foram armazenados em um índice local no PostgreSQL, sobre o qual a busca foi executada. CORE e OpenAlex foram consultados diretamente por suas APIs no momento da busca. A disponibilidade do protocolo foi testada em cada fonte, e os resultados desses testes constam no capítulo 4. [DECIDIR: ver aviso 1]

O escopo do trabalho foi delimitado a uma aplicação exclusivamente web, acessível por navegador em computadores, tablets e celulares. Ficaram fora desta versão a inclusão de outros repositórios além dos testados, o aplicativo móvel nativo, a recomendação automática de trabalhos, os alertas de novas publicações e a integração direta com gerenciadores de referências, indicados como trabalhos futuros.

4 RESULTADOS E DISCUSSÕES

Este capítulo descreve o que foi construído e o que foi observado durante o desenvolvimento e a verificação da aplicação Academic Search Hub. Os números apresentados foram medidos ou conferidos pelo autor entre 8 e 15 de outubro de 2026 e estão registrados nos arquivos de evidência do repositório do projeto. Não foi realizada medição comparativa de tempo entre a busca manual e a busca na aplicação; por isso, este trabalho não afirma que a aplicação reduz o tempo de busca, e essa comparação permanece como trabalho futuro.

4.1 APRESENTAÇÃO DO ARTEFATO DESENVOLVIDO

A aplicação foi construída como um sistema exclusivamente web, composto por uma API no servidor e uma interface que roda no navegador sem etapa de instalação. A tela inicial oferece um campo de busca, um seletor que permite pesquisar por tema ou pelo nome do autor e a lista de fontes consultadas. Após a consulta, os resultados aparecem unificados, com título, autores, ano, tipo, resumo quando existe, fonte de origem e ligação para o documento, e um resumo informa o total aproximado de resultados e quantas fontes responderam. Quando uma fonte falha, as demais continuam sendo exibidas e a falha é indicada ao usuário.

A interface permite filtrar por intervalo de anos e por tipo de publicação (artigo, tese ou dissertação, preprint, livro e outros), ordenar por relevância ou por ano e paginar os resultados. Usuários cadastrados podem salvar trabalhos nos favoritos, anotar cada favorito em texto livre, consultar e repetir o histórico de buscas, exportar resultados e gerenciar ou excluir a própria conta. A consulta como visitante, sem cadastro, é permitida.

[INSERIR AS FIGURAS: Figura 1 – Tela inicial (busca); Figura 2 – Resultados; Figura 3 – Falha parcial de fontes; Figura 4 – Filtros; Figura 5 – Favoritos e anotação; Figura 6 – Exportação; Figura 7 – Histórico; Figura 8 – Cadastro e entrada; Figura 9 – Conta e exclusão; Figura 10 – Política de privacidade. Arquivos prontos em docs/evidencias/telas/ (cada tela em largura de celular e de computador; índice em INDICE.md). Cada figura leva a legenda “Fonte: Elaborado pelo Autor (2026)”. Atenção: as capturas atuais usam dados de demonstração e não resultados reais das fontes; informe isso na legenda ou refaça com dados reais pelo roteiro ROTEIRO_REAIS.md.]

4.2 INTEGRAÇÃO, NORMALIZAÇÃO E COLETA DE DADOS

A integração seguiu a distinção entre fontes que oferecem busca por palavra-chave em sua API e fontes que oferecem apenas a coleta de metadados em lote. O OpenAlex e o CORE foram consultados ao vivo no momento da busca, cada um por meio de um conector próprio, e as consultas às fontes são feitas em paralelo, com tempo limite individual, de modo que a falha de uma não impede a resposta das demais. Os repositórios institucionais foram tratados pelo protocolo OAI-PMH descrito por Lagoze et al. (2002): como o protocolo não oferece busca por palavra-chave, os registros são colhidos periodicamente por uma ferramenta de linha de comando, gravados em um índice local no PostgreSQL e consultados nesse índice. A colheita é incremental, respeita a pausa entre requisições e lê o XML com biblioteca que bloqueia entidades externas.

A validação com respostas reais mostrou resultados distintos conforme a fonte. O OpenAlex respondeu a todos os onze casos testados (sem filtros, faixa de anos, limites abertos, quatro tipos de publicação, ordenação, paginação e combinação de filtros), com os totais conferidos em 15 de outubro de 2026. O CORE, após a obtenção de chave gratuita, também foi validado com respostas reais, e a comparação com a documentação levou a quatro ajustes no conector: os tipos de documento reais do CORE (“research article” e “journal article”) diferiam dos esperados; a consulta por autor só foi aceita sem parênteses, pois a forma com parênteses resultou em erro do servidor; as respostas passaram a excluir o texto completo, que as tornava volumosas; e o tempo limite foi ampliado para 25 segundos, porque a fonte respondeu de forma lenta. O CORE também recusou chamadas feitas em sequência rápida (código 429), o que exigiu pausa entre requisições.

Entre os repositórios por OAI-PMH, apenas o da Universidade Federal de Pernambuco (UFPE) pôde ser colhido: foram obtidos 12.366 registros, e a busca no índice local retornou resultados com resumo, autoria e tipo [CONFIRMAR o número de registros com `python -m app.harvest.cli status ufpe` no computador onde a colheita foi feita]. Esse repositório não constava entre as seis fontes previstas no início do trabalho e foi incluído por configuração justamente por ser o único que respondeu ao protocolo nas condições testadas. Os demais não puderam ser integrados por OAI-PMH. A BDTD respondeu ao endereço do protocolo com erro 404 e o portal Oasisbr com uma página de verificação anti-robô; ambos, porém, oferecem uma API REST pública própria (VuFind) que respondeu às consultas de teste, o que indica um caminho alternativo de integração, não implementado nesta versão. Para o SciELO não foi encontrado um endereço OAI-PMH que respondesse com XML. O repositório da UFPI respondeu ao protocolo, mas com índice vazio, e a verificação de certificado TLS falhou por cadeia de certificados incompleta no servidor; o da UESPI apresentou os mesmos dois problemas. Em nenhum caso a verificação de certificado foi desativada, por entender-se que isso comprometeria a segurança da coleta. As quatro fontes permanecem descritas no arquivo de configuração, desligadas, e a colheita informa a causa real da falha, em vez de uma mensagem genérica. Resolver esses dois problemas depende dos administradores dos repositórios. Esse resultado confirma, no caso concreto, a observação de Almeida e Dias (2023) de que os mecanismos de busca dos repositórios institucionais são heterogêneos e dependem de customizações de cada instituição.

A normalização seguiu o raciocínio de interoperabilidade de Chan e Zeng (2006) no nível do esquema e de Zeng e Chan (2006) no nível do registro: os campos de cada fonte foram mapeados para um modelo único (título, autores, ano, tipo, idioma, resumo, identificador, endereço e endereço do arquivo), e os tipos de cada fonte foram traduzidos para um conjunto comum. Os endereços são validados, e as entidades de caractere dos endereços (como “&amp;”) são corrigidas. Registros repetidos entre fontes são unificados por identificador (DOI) e, na falta dele, por título e ano normalizados.

A raspagem de dados, nos termos de Vargiu e Urru (2012), foi usada apenas como complemento, para completar o resumo de registros que chegaram sem ele. Ela só atua depois da busca e da deduplicação, para no máximo cinco registros por consulta, lê o arquivo robots.txt de cada domínio e não requisita o que ele proíbe, mantém pausa de dois segundos por domínio, identifica-se com o nome da aplicação e um contato, aceita apenas páginas HTML de até 1 MB e extrai somente o resumo, por meta-tags padronizadas. A raspagem foi ligada na configuração de uso, mas o seu rendimento observado foi baixo: em três tentativas reais de medição nenhum resumo foi completado, e o programa passou a registrar o motivo de cada recusa (robots.txt, erro HTTP, página que não é HTML, entre outros) para permitir investigar o resultado [CONFIRMAR: se você repetir a medição com `scripts/measure_scraping.py` e obtiver outro número, substitua esta frase pelo número medido]. Por esse motivo, a raspagem não é tratada neste trabalho como fonte de dados, mas como recurso eventual.

Por fim, a busca por autor exigiu tratamento distinto do da busca por tema. No índice local, o texto dos nomes é indexado sem redução ao radical das palavras, pois, com o radical, nomes próximos (como “Paulo” e “Paula”) seriam confundidos; no OpenAlex usou-se o filtro de nome bruto do autor, e no CORE a consulta por campo de autores. A busca apenas pelo sobrenome retorna homônimos, o que é uma limitação da busca por nome sem identificador de autor.

4.3 ARQUITETURA E TECNOLOGIAS

O servidor foi escrito em Python com o FastAPI, que, conforme a documentação de Ramírez (2018), fornece validação de dados, serialização em JSON, documentação no padrão OpenAPI e operações assíncronas; esta última característica foi decisiva para consultar várias fontes em paralelo. Os dados persistem no PostgreSQL, sistema relacional descrito por Stonebraker e Kemnitz (1991) em sua origem, escolhido por oferecer busca de texto completo com dicionário em português e remoção de acentos, usada no índice local, além de índices adequados à busca por autor. O acesso ao banco usa consultas parametrizadas, e a estrutura do banco é versionada por migrações. A interface foi escrita em HTML5, CSS3 e JavaScript, sem etapa de compilação, e os dados trafegam em JSON, formato especificado por Bray (2017).

A API segue o estilo REST de Fielding (2000): não guarda estado entre requisições (o usuário envia um token em cada chamada), usa os verbos HTTP conforme a operação e devolve códigos de status e um formato de erro único. Seguindo a preocupação de Rodríguez et al. (2016) e Palma et al. (2017) com APIs que se declaram REST sem cumprir os princípios, foi feita uma autoavaliação de cada rota quanto a quatro critérios: o verbo corresponde à operação, o caminho nomeia um substantivo no plural, o código de status é adequado e a resposta é sem estado. A avaliação foi feita pelo autor lendo o código e o OpenAPI, não é certificação e está no Quadro 1 [INSERIR o quadro de docs/API.md, seção “Autoavaliação”, com as 4 colunas e as observações]. O resultado é que todas as rotas atendem ao critério de ausência de estado e de verbo adequado, com uma ressalva (a rota de exportação por POST, que recebe os registros no corpo); o ponto fraco está na nomeação: as rotas de cadastro, entrada e exportação usam verbos no caminho (“register”, “login” e “export”) em vez de substantivos no plural, o que é justamente o antipadrão discutido por Palma et al. (2017). Esse desvio foi mantido e documentado, juntamente com a alternativa que seguiria a convenção.

4.4 INTERFACE, USABILIDADE E ACESSIBILIDADE

O layout foi concebido primeiro para o celular e ampliado para telas maiores, conforme as técnicas de design responsivo descritas por Bader e Hammouri (2016): tamanhos relativos, menu recolhível em telas pequenas, alvos de toque de pelo menos 44 por 44 pixels e ausência de rolagem horizontal a 320 pixels e com o texto ampliado a 200%.

Quanto à acessibilidade, a interface foi desenvolvida com base nas WCAG 2.1 (W3C, 2018b): idioma da página declarado, estrutura de títulos e regiões, link para pular ao conteúdo, foco visível em todos os elementos, mensagens de estado anunciadas a leitores de tela e cores que nunca são o único sinal. Os pares de cor do texto foram calculados por script e todos atingiram pelo menos 4,5:1. A verificação automática com o axe-core, em navegador real, percorreu 17 telas e estados em duas larguras (34 execuções) e não encontrou violações. Essa verificação cobre apenas parte dos critérios; por isso, o trabalho afirma que a interface atende aos critérios verificados, listados no documento de acessibilidade do projeto, e não que é plenamente conforme as WCAG 2.1. Nagaraju, Chawla e Rana (2019) [CONFIRMAR A FONTE: ver nota 4 do apêndice] discutem justamente os limites práticos desse tipo de avaliação. Não houve teste com usuários com deficiência nem com leitor de tela real.

A usabilidade foi avaliada de forma heurística, com as dez heurísticas de Nielsen (1994) [ADICIONAR NIELSEN (1994) ÀS REFERÊNCIAS e conferir a redação das heurísticas na fonte], e não com os métodos de Cybis, Betiol e Faust (2010) nem de Prates e Barbosa (2003), razão pela qual essas obras são citadas no referencial como fundamentação geral, mas não como método da avaliação. [ATENÇÃO: a avaliação foi feita por inspeção pela ferramenta de IA que auxiliou o desenvolvimento, e não por você nem por usuários. Declare isso com clareza (por exemplo: “A avaliação foi feita por inspeção, com o apoio de uma ferramenta de inteligência artificial, e confirmada pelo autor”) ou refaça a avaliação você mesmo, com os roteiros de docs/USABILIDADE.md.] Foram registrados 13 problemas: um de gravidade 3 (a política de privacidade mostrava um marcador no lugar do contato do responsável, já preenchido), quatro de gravidade 2 (laço de entrada que devolvia o usuário deslogado, título que não mencionava o histórico, anotação pendente sem sinal e ausência de aviso sobre a falta de recuperação de senha) e oito de gravidade 1. Os de gravidade 2 e 3 foram corrigidos ou mitigados, e os de gravidade 1 foram aceitos com justificativa [CONFIRMAR as contagens em docs/USABILIDADE.md, seção 2, antes de entregar]. A recuperação de senha por e-mail não foi implementada, porque exigiria envio de e-mail, o que está fora da pilha adotada, e essa é uma limitação conhecida.

4.5 FAVORITOS E EXPORTAÇÃO DE RESULTADOS

O usuário cadastrado pode salvar qualquer resultado nos favoritos, com limite por conta, sem duplicar um trabalho já salvo, e pode registrar em cada favorito uma anotação em texto livre. Santarém Segundo e Vidotti (2011) tratam da organização de objetos por tags e da folksonomia; essa organização por tags não foi implementada nesta versão, que se limita à anotação livre e a uma busca textual dentro dos favoritos. O histórico de buscas guarda as 200 consultas mais recentes de cada usuário, com o tipo de busca (tema ou autor) e os filtros, e permite repetir uma busca com um clique.

A exportação gera arquivos nos formatos BibTeX e RIS, usados por gerenciadores de referências, além de JSON e CSV, a partir dos resultados selecionados (até 100 registros) ou de todos os favoritos. A escolha desses formatos foi decisão de projeto, voltada à reutilização das referências em gerenciadores como Zotero e Mendeley, e não se apoia em uma fonte específica. A sincronização direta com esses gerenciadores não foi implementada. O arquivo CSV é protegido contra a injeção de fórmulas em planilhas.

4.6 SEGURANÇA E PRIVACIDADE (LGPD)

Segundo a Lei nº 13.709/2018 (BRASIL, 2018), o tratamento de dados deve se limitar ao mínimo necessário (art. 6º, III), e a aplicação foi projetada nessa direção: guarda apenas nome, e-mail, hash da senha (Argon2id), data e versão do consentimento, favoritos com anotações, histórico de buscas e eventos de segurança, nos quais o endereço IP é guardado apenas na forma de hash. Não há telefone, CPF, data de nascimento, cookies de rastreamento nem ferramentas de análise de uso. O texto da busca é enviado às fontes consultadas ao vivo (OpenAlex e CORE), o que consta na política de privacidade exibida no cadastro. Os direitos do art. 18 foram atendidos por rotas da API: acesso aos dados, portabilidade em arquivo JSON, correção de nome, e-mail e senha, eliminação de histórico, favoritos e da própria conta (que exige a senha) e novo aceite quando a versão da política muda.

Em relação ao OWASP (2017), cada um dos dez riscos foi mapeado para o ponto do sistema em que poderia ocorrer, o controle implementado e o teste que o confere. Entre os controles estão: consultas parametrizadas (injeção); Argon2id, mensagem única de login e limite de tentativas (autenticação); leitura de XML por biblioteca que bloqueia entidades externas (XXE); filtro de todas as consultas por usuário, com resposta 404 para recursos de terceiros (controle de acesso); cabeçalhos de segurança e política de conteúdo sem código em linha (configuração e XSS); e registro estruturado de eventos de segurança (monitoramento). Como Nunes et al. (2018) mostram que combinar ferramentas amplia a detecção, a análise estática usou quatro: bandit, semgrep, pip-audit e as regras de segurança do ruff. Na execução final de 14 de outubro de 2026, o bandit, o semgrep e o pip-audit não apontaram achados (este último sobre 86 dependências), e as regras de segurança do ruff apontaram três falsos positivos, justificados no código. Ressalta-se que ausência de achados não prova ausência de falhas, que a análise é estática e que não foram feitos testes de intrusão. Em uma das etapas, o próprio roteiro de análise reaproveitou um resultado antigo do semgrep; o defeito foi detectado, o script foi corrigido para apagar saídas anteriores e a análise foi refeita.

A verificação do conjunto foi feita por testes automatizados: em 15 de outubro de 2026, a suíte completa executou 1.235 testes aprovados e 2 ignorados, com cobertura de linhas de 98,1% do código da aplicação (3.156 linhas, 60 não cobertas) [CONFIRMAR: regenere os números com `python tasks.py test-stats` imediatamente antes de entregar].

5 CONCLUSÕES

O objetivo geral deste trabalho era desenvolver uma aplicação web que centralizasse a busca por trabalhos acadêmicos em múltiplos repositórios de acesso aberto. O objetivo foi cumprido em parte. A aplicação foi construída e entrega busca unificada por tema ou autor, filtros por ano e tipo, deduplicação, favoritos com anotação, exportação em BibTeX, RIS, JSON e CSV e uma API pública, e foi verificada por testes automatizados, análise estática e verificação de acessibilidade. Entretanto, das seis fontes inicialmente previstas, duas foram integradas por API ao vivo e validadas com respostas reais (OpenAlex e CORE), e a integração por OAI-PMH foi comprovada com um único repositório, o da UFPE, que foi incluído por não constar na lista original. O SciELO, a BDTD, a UFPI e a UESPI permaneceram descritos na configuração, mas não puderam ser colhidos por razões externas ao sistema: ausência de endereço OAI-PMH que respondesse, bloqueio anti-robô, índice vazio e cadeia de certificados incompleta. Portanto, o objetivo de centralizar a busca na UESPI e na UFPI não foi atingido nesta versão.

Também não foi medido o ganho de tempo em relação à busca manual, de modo que não se pode afirmar que a aplicação reduz o esforço do estudante; apenas foi demonstrado que a consulta única às fontes ativas devolve resultados unificados e sem duplicatas. A avaliação de usabilidade foi heurística, sem participantes, e a de acessibilidade foi automática, sem testes com leitores de tela, o que limita as conclusões sobre a experiência real de uso. A raspagem complementar de resumos teve rendimento baixo nas tentativas realizadas. As rotas de cadastro, entrada e exportação não seguem a convenção de nomes no plural, e não há recuperação de senha.

Como perspectivas para a continuidade do projeto, sugerem-se as seguintes evoluções:

- Fontes institucionais: resolver, junto aos administradores dos repositórios da UFPI e da UESPI, o índice vazio e a cadeia de certificados, e integrar a BDTD e o Oasisbr por sua API REST pública (VuFind), já que o OAI-PMH não está disponível para eles.

- Medição de tempo: comparar o tempo de busca manual e na aplicação, com participantes e consultas definidas, para sustentar ou não a redução de esforço.

- Avaliação com usuários: aplicar teste de usabilidade com estudantes da UESPI e verificação de acessibilidade com leitor de tela.

- Aplicativo móvel nativo: desenvolver versões para Android e iOS a partir da API pública já disponível.

- Recomendação de trabalhos: sugerir publicações relacionadas com base no histórico de buscas e nos favoritos do usuário.

- Alertas: avisar o usuário, por e-mail ou notificação, quando houver novas publicações sobre um tema salvo; o mesmo recurso viabilizaria a recuperação de senha.

- Gerenciadores de referências e tags: sincronizar os favoritos diretamente com ferramentas como Zotero e Mendeley e organizar os favoritos por tags.

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
