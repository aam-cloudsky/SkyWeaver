Você não está perdido no sentido ruim. Você está esbarrando numa distinção que realmente precisa ser formalizada: `unit`, `layer`, `scenario`, `parcel` não são a mesma coisa, e hoje parte da confusão vem de o código já ter uma mecânica forte para `units`, mas ainda não ter uma mecânica explícita para `layers`.

O ponto central é este:

- `Unit` responde a: “quem processa?”
- `Parcel` responde a: “qual dado circula?”
- `Layer` responde a: “qual aspecto semântico do cenário está sendo representado?”
- `Scenario` responde a: “qual conjunto coerente de estado existe ao mesmo tempo?”

Essa separação já ajuda bastante.

**Minha leitura do que está acontecendo hoje**

Hoje o projeto está muito forte em `processamento` e `sincronização`:
- `OperationalUnit`
- `Outpost`
- `Depot`
- `Parcel`

Mas está fraco em `organização semântica do mundo`.

Por isso você sente que:
- heliports ficam numa unit
- cost map ficaria em outra
- restrições em outra
- droneports em outra
- e a noção de “camada do cenário” fica só implícita na sua cabeça

Isso é um sintoma arquitetural real: o sistema tem boa mecânica operacional, mas ainda não tem um modelo semântico explícito para layers.

## O que eu acho que **não** deve acontecer

Eu não transformaria `layer` em sinônimo de `unit`.

Isso seria conceitualmente errado na maior parte dos casos.

Porque:

- `layer` é estado semântico
- `unit` é comportamento / transformação

Exemplo:
- “heliports” é uma layer
- `SourcesUnit` não é uma layer; ela produz ou carrega layers
- `RestrictionUnit` não é uma layer; ela transforma o grid com base em layers
- `RoutesUnit` não é uma layer; ela deriva estruturas de rota a partir de layers e outras estruturas

Então, se você misturar isso, a arquitetura tende a ficar opaca.

## O que eu acho que **sim** faz sentido

Faz sentido formalizar `Layer` como uma categoria conceitual acima de `Parcel`, mas abaixo de `Scenario`.

Uma boa hierarquia seria:

- `Scenario`
  - conjunto completo de estado de um caso de execução
- `Layer`
  - recorte temático dentro do cenário
- `Parcel`
  - unidade concreta de dado publicada no sistema
- `Unit`
  - transformador de parcels/layers

Em termos conceituais:

```text
Scenario
  ├── Infrastructure Layer
  │     ├── HeliportsParcel
  │     ├── VertiportsParcel
  │     └── DomainParcel
  ├── Cost Layer
  │     ├── CellCostParcel
  │     └── RiskCostParcel
  ├── Restriction Layer
  │     ├── RestrictedCellsParcel
  │     └── NoFlyZonesParcel
  ├── Routing Layer
  │     ├── AirspaceGraphParcel
  │     ├── RoutesGraphParcel
  │     └── TerminalsGraphParcel
```

Isso é bem mais limpo.

## A melhor decisão para agora

Eu **não** criaria `Section` nem `Scenario` agora como mecanismo completo no core.

Você mesmo já percebeu isso. E eu concordo.

Porque `Scenario` muda a unidade de isolamento do sistema inteiro:
- deixa de existir “um depot do processo”
- passa a existir “um depot por cenário”
- isso afeta lifecycle, registry, validity, orchestration, talvez até visualização

É uma mudança grande. Boa, mas grande.

Para agora, eu seguiria este caminho:

### Caminho recomendado
1. Manter `units` como estão, como executores.
2. Formalizar `layer` primeiro só como conceito de modelagem.
3. Mapear cada `parcel` para uma `layer`.
4. Só depois pensar se vale dar forma de código a isso.

Ou seja: primeiro documentar e classificar. Depois mecanizar.

## Como eu classificaria o projeto hoje

Eu faria uma tabela mental assim:

- `SourcesUnit`
  - produz parcels da layer `geodata`
- `DomainUnit`
  - produz parcels da layer `domain`
- `AlignmentUnit`
  - produz parcels da layer `aligned infrastructure`
- `HexGridUnit`
  - produz parcels da layer `grid substrate`
- `RestrictionUnit`
  - muta/aplica layer `restrictions`
- `RoutesUnit`
  - produz parcels da layer `routing`
- `VisualizationUnit`
  - consome múltiplas layers, mas não é layer

Perceba o ganho: a unit continua existindo, mas ela passa a ser entendida como operando sobre layers.

## Então algumas units deveriam virar layers?

Na minha opinião: **não**.

Algumas units deveriam passar a ser entendidas como **operadores de layers**.

Essa frase é importante.

Exemplo:
- `SourcesUnit` é operadora de ingestão
- `RestrictionUnit` é operadora de imposição de restrições
- `RoutesUnit` é operadora de derivação de rede
- `VisualizationUnit` é operadora de apresentação

Isso preserva a clareza.

## O que eu faria de forma incremental

Eu começaria sem mudar o core.

### Etapa 1
Criar uma documentação simples dizendo:

- quais layers existem hoje
- quais parcels pertencem a cada layer
- quais units produzem/consomem essas layers

Isso já resolve 70% da confusão.

### Etapa 2
Se isso se mostrar útil, criar um metadado de layer nos parcels ou nos outposts.

Exemplo conceitual:

```python
@dataclass
class HeliportsParcel(Parcel):
    LAYER = "infrastructure"
```

ou

```python
metadata={"role": ParcelRole.CONSUMED, "layer": "infrastructure"}
```

Sem mudar a mecânica. Só tornando a semântica explícita.

### Etapa 3
Só muito depois pensar em `Scenario` / `Section`.

## Sobre `Scenario` e `Section`

A ideia é boa. Conceitualmente forte.

Um `Scenario` seria algo como:
- um conjunto fechado de parcels
- representando um estado de mundo
- podendo coexistir com outros cenários

Isso é útil para:
- comparar configurações
- testar políticas
- rodar simulações paralelas
- manter múltiplos ambientes

Mas isso é outra escala arquitetural.

Hoje o seu sistema está no nível:
- “como um cenário é representado e transformado?”

`Scenario` entra no nível:
- “como múltiplos mundos coexistem no sistema?”

Essa é a razão de eu adiar.

## Minha recomendação objetiva

Se eu tivesse que te orientar com firmeza, seria isto:

1. Não transforme `layer` em `unit`.
2. Não implemente `Scenario/Section` agora.
3. Formalize `layer` primeiro como conceito documental.
4. Se funcionar bem, adicione metadado de `layer` aos parcels.
5. Só depois avalie se vale criar um `Layer` como objeto real no código.

## Conceito-chave

Em GIS, layer é uma **organização semântica do mundo**. Em software, unit é uma **organização operacional do comportamento**. Misturar os dois costuma gerar confusão porque uma coisa responde “o que o mundo contém” e a outra responde “o que o sistema faz”.

## Dica de aprendizado

Tente fazer este exercício num papel, antes de codar:
- liste todos os parcels atuais
- agrupe por layer
- ao lado, escreva qual unit produz
- ao lado, escreva quais units consomem

Se essa tabela ficar estável e útil, então a abstração de `layer` merece entrar no código. Se não ficar, ela ainda está cedo demais.

Se você quiser, eu posso fazer agora a próxima etapa útil: te entregar uma proposta de `LAYERS.md` para o projeto, classificando os parcels e units atuais por layer, sem mexer na arquitetura ainda.