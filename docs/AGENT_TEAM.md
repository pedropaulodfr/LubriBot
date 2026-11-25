# Equipe de agentes

## Composição

| # | Agente | Especialidade | Escopo de escrita |
|---|---|---|---|
| 01 | Tech Lead / Arquiteto | arquitetura, integração, aprovação final | `docs/`, revisão de tudo |
| 02 | Python | código e estrutura da aplicação | `lubribot/**`, `handlers/**`, `services/**` |
| 03 | Banco de dados | modelos, migrações, consultas, Supabase | `lubribot/models/**`, `lubribot/repositories/**`, `lubribot/database/**`, `migrations/**` |
| 04 | Telegram / UX | fluxos, teclados, mensagens | `lubribot/bot/**`, `keyboards/**` |
| 05 | Performance | medições, pool, N+1, I/O | `lubribot/database/**` (com BD), `lubribot/integrations/**` |
| 06 | Segurança | autorização, validação, segredos | `lubribot/schemas/**`, middlewares |
| 07 | QA / Reviewer | testes e revisão independente | `tests/**` |
| 08 | Documentação | README, docs, changelog, runbook | `docs/**`, `README.md` |

## Regras de colaboração

1. Cada agente recebe escopo definido e não escreve fora dele.
2. Ninguém altera regra de negócio sem autorização explícita do dono.
3. O Tech Lead revisa e integra; QA valida de forma independente.
4. Alterações críticas (notificação, autorização, schema) exigem revisão do QA
   antes de considerar concluídas.
5. Conflito de arquivo é resolvido por quem é dono da pasta, não por ordem de
   chegada.
6. Toda entrega precisa de evidência: teste, log ou consulta que comprove.

## O que aconteceu nesta sessão

- **Fase 1 (auditoria):** sete subagentes especializados foram disparados em
  paralelo (Python, banco, UX, performance, segurança, QA, docs). **Todos
  falharam sem mensagem final**, sem resultado parcial recuperável. A auditoria
  foi executada diretamente pelo Tech Lead, lendo o código, o SQL e o Git.
- **Efeito:** a revisão independente prevista (QA separado) **não aconteceu** na
  auditoria. Isso está registrado como dívida: a fase F5 deve ter revisão
  independente dos handlers reescritos.
- **Fase 2 (implementação):** executada pelo Tech Lead, porque a rota de
  subagentes falhou duas vezes na mesma sessão (custo: ~2 h de espera sem
  entregas). Decisão pragmática, registrada aqui para transparência.

## Estado dos agentes na fase 2

| Agente | Atuou? | Observação |
|---|---|---|
| 01 Tech Lead | sim | fundação, notificações, migrações, docs, integração |
| 02 Python | absorvido | handlers corrigidos pelo lead |
| 03 Banco | absorvido | modelos + Alembic pelo lead |
| 04 UX | parcial | correções de integridade nos fluxos, sem redesign |
| 05 Performance | parcial | pool, selectin, consultas em lote |
| 06 Segurança | parcial | autorização por dono, segredos, validação |
| 07 QA | **não** | suíte escrita pelo lead; falta revisão independente |
| 08 Docs | absorvido | README + `docs/` |

## Recomendação para a próxima fase

Re-disparar subagentes com escopos menores e artefato de saída obrigatório
(arquivo ou relatório curto), por exemplo:

- QA: revisar `handlers/*` reescritos e apontar divergências de comportamento;
- UX: propor novo mapa de menu e textos;
- Performance: medir p50/p95 por comando com banco de teste.

Se a rota de subagentes continuar instável, manter a execução sequencial pelo
lead e registrar o desvio, como feito aqui.
