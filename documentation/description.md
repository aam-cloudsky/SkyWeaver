**Visão Geral**

O código foi construído em torno de uma ideia muito clara: separar o sistema em **unidades operacionais** que não trocam dados diretamente entre si, mas se coordenam por meio de um estado compartilhado e tipado. Esse estado compartilhado é o `Depot`, e a interface declarativa de cada unidade com esse estado é o `Outpost`. Em termos de intenção, o projeto tenta evitar acoplamento direto entre módulos como `sources`, `domain`, `hexgrid`, `routes` e `visualization`, substituindo chamadas ad hoc por um contrato explícito de entrada e saída.

A peça central dessa arquitetura está em [outpost.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/core/logistics/outpost.py) e [depot.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/core/logistics/depot.py). O `Depot` é o “ground truth” dos `Parcels`. O `Outpost` declara, via dataclass e `metadata={"role": ...}`, quais `Parcels` uma unidade consome, produz ou apenas muta. A intenção é muito boa: transformar dependências implícitas em um schema explícito.

**Como o sistema foi pensado**

O padrão conceitual dominante é:

1. Um `OperationalUnit` executa uma transformação.
2. Ele lê insumos do seu `Outpost`.
3. Ele publica resultados de volta no `Outpost`.
4. O `Outpost` sincroniza com o `Depot`.
5. O `Sentinel` observa essa troca e mantém a validade dos dados derivados.

Isso aparece de forma limpa no pipeline principal:
- [yaml_loader_unit.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/yaml_loader/yaml_loader_unit.py): carrega configuração.
- [sources_unit.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/sources/sources_unit.py): obtém geodados reais ou simulados.
- [domain_unit.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/domain/domain_unit.py): constrói o domínio operacional.
- [alignment_unit.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/geodata_domain_alignment/alignment_unit.py): projeta os dados para o frame local do domínio.
- [hexgrid_unit.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/hexgrid/hexgrid_unit.py): discretiza o espaço em células hexagonais.
- [restriction_unit.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/restriction/restriction_unit.py): aplica restrições duras no grid.
- [routes_unit.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/routes/routes_unit.py): computa os grafos e as rotas.
- [viz_unit.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/visualization/viz_unit.py): renderiza o estado e interage com o usuário.

A camada de aplicação atual, em [routes_app.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/application/routes_app.py), faz a orquestração prática desse pipeline. Ela ainda é pragmática e específica do caso de uso, mas cumpre o papel de decidir a ordem de execução dos `units` e de aplicar regras de interação.

**Arquitetura atual**

Hoje a arquitetura está em três camadas principais.

- `core`
  - Infraestrutura do sistema: mensagens, `Depot`, `Outpost`, `Parcel`, ciclo de vida, validade.
- `units`
  - Capacidades do domínio, cada uma encapsulada em uma unidade operacional.
- `application`
  - Orquestração de alto nível e regras de uso da interface.

A melhor forma de descrever isso é: **arquitetura orientada a dados compartilhados, com unidades modulares e sincronização mediada por outposts**.

O `OperationalUnit`, em [operational_unit.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/core/operations/operational_unit.py), é propositalmente mínimo. A intenção parece ser: “unidade operacional não é um framework pesado; é só um executor com `run()` e um outpost associado”. Isso é simples e coerente com o resto do sistema.

**Padrões usados**

Os principais padrões que aparecem no código são:

- `Data-oriented architecture`
  - O foco é mais nos `Parcels` e no fluxo de estado do que em objetos ricos e fortemente acoplados.
- `Ports and adapters`, de forma informal
  - O `Outpost` funciona como porta declarativa da unidade.
- `Publish/subscribe`
  - O `Depot` e o barramento interno coordenam atualização e sincronização.
- `Single source of truth`
  - O `Depot` é a autoridade sobre o estado compartilhado.
- `Pipeline processing`
  - O sistema transforma dados em estágios sucessivos.
- `Application layer`
  - Em [routes_app.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/application/routes_app.py) e nos experimentos com intents, existe a tentativa de separar UI, política e execução.

Também há um uso consistente de `dataclass` para schema e transporte de dados. Isso reforça a intenção de tornar o sistema declarativo.

**Intenção dos componentes principais**

- `Parcel`
  - Unidade semântica de dado. Não é “qualquer estrutura”; é algo publicável e rastreável dentro do sistema.
- `Outpost`
  - Contrato de IO de uma unidade. Declara o que ela consome, produz e muta.
- `Depot`
  - Registro compartilhado dos parcels atuais.
- `Sentinel`
  - Mecanismo de validade/invalidação incremental. Em [sentinel.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/core/logistics/validity/sentinel.py), ele invalida derivados quando insumos mutáveis mudam.
- `OperationalUnit`
  - Processo que transforma estado do sistema.
- `GraphPack`
  - Envelope semântico para grafos do `igraph`, com mapas explícitos entre célula e vértice, em [graph_pack.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/routes/graph/graph_pack.py).

Esse último ponto é importante: `GraphPack` existe para impedir que o código de domínio fique “adivinhando” IDs internos do `igraph`. Isso foi uma boa decisão conceitual.

**Como o roteamento foi modelado**

O subsistema de rotas está organizado assim:

- [hexgrid.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/hexgrid/structure/hexgrid.py) e [hexcell.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/hexgrid/structure/hexcell.py)
  - representam o espaço discreto e o custo/estado das células.
- [graph_builder.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/routes/graph/graph_builder.py)
  - produz três níveis de grafo:
  - `AirspaceGraphPack` (`G0`): conectividade base do espaço navegável.
  - `RoutesGraphPack` (`G1`): união das rotas entre terminais.
  - `TerminalsGraphPack` (`G2`): conectividade terminal-terminal.
- [routing.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/routes/routing.py)
  - calcula shortest paths entre pares de terminais.
- [metrics.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/analysis/metrics.py)
  - calcula métricas sobre os caminhos já encontrados.

A intenção atual é tratar `G0` como topologia base e usar o cálculo de custo no momento do roteamento. Isso aparece no comentário de [graph_builder.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/routes/graph/graph_builder.py): “Topology only. Weight computation should not live here.” Esse é um sinal importante da direção que o código está tomando.

**Estado atual da qualidade arquitetural**

Os pontos fortes hoje são:

- A arquitetura tem uma ideia central forte e consistente.
- O sistema explicita dependências via `Outpost`, em vez de escondê-las em chamadas arbitrárias.
- O domínio espacial está relativamente bem separado do domínio de infraestrutura.
- O uso de `GraphPack` e `Domain` mostra preocupação real com semântica, não só com funcionamento.
- Há uma tentativa clara de construir uma base onde módulos futuros possam ser acoplados sem colapsar tudo em scripts.

Os riscos atuais são:

- A camada de aplicação ainda está incompleta e um pouco híbrida.
  - [routes_app.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/application/routes_app.py) é o fluxo real.
  - [hex_app_controller.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/application/hex_app_controller.py), [intent.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/application/intent.py) e [dispatcher.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/application/dispatcher.py) parecem um experimento de arquitetura de intents ainda não consolidado.
- Existem sinais de transição/refatoração em andamento.
  - nomes antigos, comentários de TODO, papéis de parcelas ainda em revisão, APIs incompletas.
- Algumas regras de negócio ainda estão espalhadas entre `app`, `viz` e `routes`.
  - isso é normal em fase exploratória, mas é justamente o tipo de coisa que daqui a 3 meses fica difícil de reconstruir.
- Há certa tensão entre “estado derivado no depot” e “estado local incremental em uma unit”.
  - o melhor exemplo é [restriction_unit.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/restriction/restriction_unit.py), que guarda `_prev_heliport_cells` localmente.

**Leitura da intenção do projeto**

A intenção por trás do desenho me parece ser esta:

- O projeto quer ser um sistema modular de planejamento/roteamento aéreo urbano.
- O espaço aéreo é tratado como uma verdade única.
- Tudo que é derivado desse espaço deve ser publicável, rastreável e invalidável.
- Os módulos devem ser acoplados por contrato de dados, não por dependência direta.
- A camada superior deve orquestrar comportamento e política, não os `units`.

Essa intenção está bem refletida no código, mesmo com arestas ainda abertas.

**Como eu descreveria a arquitetura em uma frase**

Eu documentaria assim:

> SkyWeaver é um sistema orientado a parcels e outposts, no qual unidades operacionais independentes transformam estado espacial compartilhado, sincronizado por um depot central e validado por um sentinel, formando um pipeline modular de geodata, domínio, discretização, restrição, roteamento, análise e visualização.

**O que você provavelmente quis preservar com esse desenho**

Se daqui a 3 meses você abrir esse código, o que vale lembrar é:

- Você não estava tentando só “fazer rodar”.
- Você estava tentando construir uma arquitetura onde:
  - cada módulo sabe o que consome e o que produz;
  - o estado compartilhado é observável e validável;
  - grafos, grid e geodata sejam derivados claros de um mesmo espaço;
  - a aplicação de regras do usuário fique acima dos `units`.

Isso é uma direção madura. O custo é que a arquitetura fica mais exigente com disciplina.

**Sugestão de documentação-base**

Se eu transformasse isso em documentação oficial do projeto, eu dividiria em 5 seções:

1. `Core concepts`
   - `Parcel`, `Outpost`, `Depot`, `Sentinel`, `OperationalUnit`.
2. `Execution model`
   - como um `unit` lê, transforma e publica.
3. `Spatial pipeline`
   - `YAML -> Sources -> Domain -> Alignment -> HexGrid -> Restriction -> Routes -> Visualization`.
4. `Routing model`
   - `G0`, `G1`, `G2`, `GraphPack`, shortest paths e métricas.
5. `Application layer`
   - quem orquestra, onde regras de interação devem viver, e o que não deve ficar nos `units`.

**Resumo final**

Hoje o projeto já tem uma arquitetura real, não apenas um conjunto de scripts. O núcleo é um sistema de sincronização declarativa de dados entre módulos especializados. O desenho é bom, a intenção é forte e bastante coerente. O estado atual ainda é de exploração guiada por uma boa abstração, não de arquitetura estabilizada. O principal trabalho futuro não é “inventar outra arquitetura”, mas consolidar a camada de aplicação e reduzir as zonas híbridas em que regras ainda estão espalhadas.

Se você quiser, no próximo passo eu posso te entregar isso já no formato de um `ARCHITECTURE.md`, com seções, linguagem mais formal e já pronto para entrar no repositório.