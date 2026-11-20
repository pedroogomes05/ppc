# Decisão sobre a topologia do ensaio

## Topologia escolhida

Para o ensaio com as duas máquinas disponíveis, a configuração prática escolhida é:

```text
Windows: k6
Mac:     agregador Spring Boot + stub HTTP
```

O k6 envia pedidos ao agregador no Mac. O agregador chama o stub localmente, através de `localhost:8080`.

## Motivo da decisão

A proposta prevê que o agregador corra no portátil com macOS e que o gerador de carga corra noutra máquina. Não especifica em que máquina deve correr o stub.

Nos testes de conectividade realizados, o Windows conseguiu contactar o agregador no Mac: o pedido a `/aggregate/platform` recebeu uma resposta HTTP 500. Isso demonstra que o pedido chegou à aplicação; o erro ocorreu depois, quando o agregador tentou comunicar com o stub.

Na direção inversa, o stub respondeu a pedidos locais no Windows, mas o Mac não conseguiu aceder a `192.168.1.149:8080`: a ligação expirou. Foi criada uma regra de firewall para permitir TCP na porta 8080 a partir do Mac, e confirmou-se que o stub estava à escuta e que a regra correspondia ao endereço e à porta esperados. Mesmo assim, a ligação continuou a expirar.

Colocar o agregador e o stub no Mac evita essa ligação entre máquinas que está a falhar. Manter o k6 no Windows preserva a separação do gerador de carga prevista na proposta e usa a direção de ligação que já foi confirmada entre os computadores.

## Possível influência nos resultados

Esta decisão é um compromisso prático e pode afetar as medições:

- O agregador e o stub passam a partilhar CPU, memória, sistema operativo, recolha de lixo e recursos de rede.
- O stub espera 1 000 ms por pedido e está configurado para usar virtual threads. Como passa a maior parte do tempo à espera, espera-se que o consumo de CPU seja reduzido, mas isso não elimina a utilização de memória, logging, escalonamento e outros custos.
- A chamada entre agregador e stub passa a usar a interface local (`localhost`) em vez da rede entre computadores. A latência e os custos dessa comunicação serão diferentes.
- A contenção entre os dois serviços pode variar com a carga e pode afetar throughput e latências, incluindo p95 e p99. Não se deve assumir que o efeito é igual nos três modelos de concorrência.

Por isso, os resultados devem ser descritos como obtidos com **agregador e stub co-localizados no Mac e k6 numa máquina Windows separada**. A topologia permite comparar os três endpoints nas mesmas condições gerais, mas não representa um deployment com o stub num host remoto independente.

## Como reduzir e documentar o risco

1. Manter o stub e o agregador na mesma máquina durante todas as condições e repetições.
2. Manter constantes o atraso de 1 000 ms, a configuração de virtual threads do stub, as versões de Java e as restantes opções do ensaio.
3. Registar, se possível, o uso de CPU e memória no Mac durante cada execução, e confirmar que o Windows consegue manter a carga do k6 sem erros ou falta de VUs.
4. Incluir esta co-localização como ameaça à validade e evitar generalizar os resultados para serviços distribuídos em máquinas independentes.

Esta decisão pode ser revista se a comunicação Mac→Windows na porta 8080 ficar disponível ou se houver acesso a uma terceira máquina para alojar o stub separadamente.
