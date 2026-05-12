SET session_replication_role = 'replica';

INSERT INTO public."usuarios" ("id", "telegram_id", "perfil", "primeiroNome", "ultimoNome", "usuarioNome", "CPF", "foto", "email", "telefone", "status") VALUES (1, 1493144474, 'Proprietario', 'Pedro Paulo', '', 'pedro383828', NULL, NULL, NULL, NULL, 'Ativo') ON CONFLICT ("id") DO NOTHING;

INSERT INTO public."usuarioparametros" ("id", "usuario_id", "receberNotificacoes", "diasNotificacao") VALUES (1, 1, True, 10) ON CONFLICT ("id") DO NOTHING;

INSERT INTO public."veiculos" ("id", "usuario_id", "tipo", "placa", "renavam", "fabricante", "modelo", "anoModelo", "anoFabricacao", "cor", "status") VALUES (1, 1, 'Moto', 'RGH6F20', '01284111501', 'Honda', 'Bros 160', '2022', '2021', 'Vermelha', 'Ativo') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."veiculos" ("id", "usuario_id", "tipo", "placa", "renavam", "fabricante", "modelo", "anoModelo", "anoFabricacao", "cor", "status") VALUES (2, 1, 'Carro', 'RTF6699', NULL, 'Chevrolet', 'Cruze Limited', '2022', '2021', 'Branca', 'Deletado') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."veiculos" ("id", "usuario_id", "tipo", "placa", "renavam", "fabricante", "modelo", "anoModelo", "anoFabricacao", "cor", "status") VALUES (3, 1, 'Moto', 'MYY7583', '00964201283', 'Honda', 'Bros 150', '2008', '2008', 'Vermelha', 'Ativo') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."veiculos" ("id", "usuario_id", "tipo", "placa", "renavam", "fabricante", "modelo", "anoModelo", "anoFabricacao", "cor", "status") VALUES (4, 1, 'Carro', 'NQS6H35', '01239481540', 'Toyota', 'Yaris', '2021', '2020', 'Cinza', 'Ativo') ON CONFLICT ("id") DO NOTHING;

INSERT INTO public."servicos" ("id", "descricao", "status", "usuario_id") VALUES (1, 'Troca de Óleo', 'Ativo', NULL) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."servicos" ("id", "descricao", "status", "usuario_id") VALUES (3, 'Revisão', 'Ativo', NULL) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."servicos" ("id", "descricao", "status", "usuario_id") VALUES (4, 'Teste', 'Excluido', 1) ON CONFLICT ("id") DO NOTHING;

INSERT INTO public."produtos" ("id", "descricao", "status", "usuario_id") VALUES (1, 'Mobil super moto 10w30 - óleo semi sintético', 'Ativo', 1) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."produtos" ("id", "descricao", "status", "usuario_id") VALUES (2, 'Pastilha de freio dianteira', 'Ativo', 1) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."produtos" ("id", "descricao", "status", "usuario_id") VALUES (3, 'Pastilha de freio traseira', 'Ativo', 1) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."produtos" ("id", "descricao", "status", "usuario_id") VALUES (4, 'Vela ignição', 'Ativo', 1) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."produtos" ("id", "descricao", "status", "usuario_id") VALUES (6, 'Filtro de combustível', 'Ativo', 1) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."produtos" ("id", "descricao", "status", "usuario_id") VALUES (7, 'Arruela bujão óleo', 'Ativo', 1) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."produtos" ("id", "descricao", "status", "usuario_id") VALUES (5, 'Filtro de Ar', 'Ativo', 1) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."produtos" ("id", "descricao", "status", "usuario_id") VALUES (8, 'Junta guarnição', 'Ativo', 1) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."produtos" ("id", "descricao", "status", "usuario_id") VALUES (9, 'Óleo telescópio', 'Ativo', 1) ON CONFLICT ("id") DO NOTHING;

INSERT INTO public."veiculodica" ("id", "veiculo_id", "texto", "datacriacao") VALUES (1, 1, 'Aqui vão umas dicas rápidas pra sua Bros 160 ser sua parceira por muito tempo!

*   **Óleo Motor:** Troque o óleo a cada 3.000 km ou 6 meses, o que vier primeiro. Use o tipo exato do manual. Vida longa ao motor! 🏍️💨
*   **Pneus:** Calibre semanalmente com a pressão do manual. Fique de olho no desgaste; pneu careca é perigoso e aumenta o consumo. 📏⚠️
*   **Relação (Corrente):** Limpe e lubrifique a cada 500 km ou após chuva/terra. Ajuste a folga corretamente para evitar desgaste. ⛓️✨
*   **Freios:** Verifique o nível do fluido e o desgaste de pastilhas/lonas. Barulho estranho? Procure um mecânico. Sua segurança em primeiro! 🛑
*   **Filtro de Ar:** Limpe ou troque o filtro de ar a cada 10.000 km, ou antes se rodar muito empoeirado. Melhora desempenho e consumo! 🌬️
*   **Bateria:** Mantenha os terminais limpos e apertados. Se a moto custar a pegar, pode ser um sinal de que ela precisa de atenção. 🔋⚡
*   **Luzes:** Confira farol, lanterna e piscas regularmente. Iluminação em dia é segurança pra você e pra evitar multas. 🚦💡
*   **Limpeza Geral:** Lave sua Bros com frequência, principalmente após terra/chuva. Use produtos neutros. Mantém a moto bonita e protege! 🧼🚿
*   **Revisões Programadas:** Siga o plano de revisões da Honda. É essencial para a garantia, performance e evitar gastos inesperados. 🛠️💰', '2026-01-03') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."veiculodica" ("id", "veiculo_id", "texto", "datacriacao") VALUES (2, 3, '*   <b>Óleo do Motor:</b> Troque religiosamente a cada 1.500-2.000km com o tipo correto. É o sangue da sua Bros! 🩸 Garante longa vida útil e bom desempenho.
*   <b>Corrente de Transmissão:</b> Limpe e lubrifique a cada 500km. Verifique a folga regularmente. Evita desgaste prematuro e ruídos. ✨
*   <b>Pneus:</b> Calibre semanalmente na pressão indicada no manual. Inspecione o desgaste para sua segurança e economia de combustível. 🏍️💨
*   <b>Freios:</b> Cheque pastilhas/lonas e o nível do fluido (se aplicável) com frequência. Essencial para sua segurança! 🛑
*   <b>Filtro de Ar:</b> Limpe ou troque a cada 4.000-6.000km. Um filtro limpo melhora a respiração do motor, dando mais força e economia. 🌬️
*   <b>Limpeza:</b> Lave sua moto frequentemente com produtos neutros. Remove a sujeira, protege a pintura e previne ferrugem. Uma Bros limpa é uma Bros feliz! 🧼
*   <b>Revisões:</b> Siga o plano do manual. Leve a um mecânico de confiança para as revisões periódicas. Previne problemas, reduz custos e mantém o valor. 🛠️', '2026-01-07') ON CONFLICT ("id") DO NOTHING;

INSERT INTO public."veiculodiagnosticos" ("id", "veiculo_id", "problema", "diagnostico", "datacriacao", "resolvido", "util") VALUES (1, 3, 'A moto dá partida mas quando acelera morre', 'Moto Bros 150 (2008) dá partida mas morre ao acelerar? Isso aponta para falhas na alimentação ou ignição. 🏍️

<b>1. Possíveis Causas:</b>
*   <b><u>Carburador Sujo:</u></b> Giclês entupidos não entregam combustível suficiente ao acelerar. ⛽
*   <b><u>Filtro de Ar Bloqueado:</u></b> Falta de ar gera mistura rica, "afogando" a moto. 🌬️
*   <b><u>Vela de Ignição Fraca:</u></b> Faísca insuficiente em altas rotações. 🔥
*   <b><u>Combustível Ruim:</u></b> Água ou sujeira impede a queima correta. 💧
*   <b><u>Entrada Falsa de Ar:</u></b> Mangueiras ressecadas desregulam a mistura. 🍃

<b>2. Passos de Solução:</b>
*   <b>Filtro de Ar:</b> Limpe-o ou troque-o. É um passo simples e pode resolver! 💨
*   <b>Vela de Ignição:</b> Verifique, limpe ou troque e ajuste a folga. ✨
*   <b>Combustível:</b> Drene o tanque e reponha com gasolina nova e de boa qualidade. ⛽
*   <b>Carburador:</b> Se os anteriores falharem, a limpeza interna é essencial. 🛠️

<b>3. Manutenção Preventiva:</b>
*   Sempre use combustível de qualidade e de boa procedência. 🛡️
*   Mantenha os filtros de ar e a vela sempre em dia, trocando periodicamente. 📅
*   Faça revisões periódicas completas em sua moto. 🧑‍🔧

<b>4. Mecânico Profissional?</b>
*   Sim, se as verificações básicas (filtro de ar, vela e combustível) não resolverem o problema. ⚠️ A limpeza complexa do carburador, ajustes finos ou outros diagnósticos mais profundos exigem conhecimento e ferramentas específicas. É crucial para a segurança e durabilidade da moto! 👨‍🔧', '2026-01-17', True, NULL) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."veiculodiagnosticos" ("id", "veiculo_id", "problema", "diagnostico", "datacriacao", "resolvido", "util") VALUES (34, 3, 'Pancadas na traseira ao passar em buracos ou lombadas', 'Problema: Pancadas na traseira ao passar em buracos ou lombadas na sua Moto Honda Bros 150 (2008). 🛠️

<b>1. Possíveis causas:</b>
*   <b>Amortecedor traseiro:</b> Causa mais comum. Pode estar vazando óleo, sem pressão ou com a mola "cansada". A moto "bate seco" no fim do curso. 📉
*   <b>Buchas da balança (pro-link):</b> Gastas ou ressecadas, geram folga e ruídos na suspensão. ⚙️
*   <b>Rolamentos da roda traseira:</b> Com folga, causam instabilidade e batidas leves. 🔗
*   <b>Parafusos soltos:</b> Fixações do amortecedor ou da balança frouxas. 🔩

<b>2. Passos para solucionar:</b>
*   <u>Inspeção visual:</u> Verifique o amortecedor traseiro (vazamentos de óleo, mola quebrada/danificada). 👀
*   <u>Checar folgas:</u> Com a traseira levantada, movimente a roda (rolamentos) e a balança (buchas). Não deve haver folga excessiva. 🧐
*   <u>Pressão dos pneus:</u> Garanta que o pneu traseiro esteja com a pressão correta conforme o manual. Pneu muito cheio amplifica a pancada. 💨

<b>3. Manutenção preventiva:</b>
*   Faça inspeções regulares na suspensão, balança e buchas. 🗓️
*   Mantenha os pontos de pivô da balança lubrificados. 🧴
*   Verifique semanalmente a pressão e condição dos pneus. 🚲
*   Evite sobrecarga e passar em buracos em alta velocidade. ⚠️

<b>4. Mecânico ou DIY?</b>
*   <u>DIY:</u> Você pode realizar a inspeção visual básica e checar a pressão dos pneus. 👍
*   <u>Mecânico:</u> Qualquer suspeita de falha no amortecedor, buchas da balança, rolamentos ou parafusos estruturais exige um profissional. São peças cruciais para a segurança e controle. 🧑‍🔧', '2026-02-17', True, NULL) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."veiculodiagnosticos" ("id", "veiculo_id", "problema", "diagnostico", "datacriacao", "resolvido", "util") VALUES (35, 4, 'O veículo, principalmente na subida de serras, quando sobe com o ar condicionado ligado, a luz do arrefecimento acende. Mesmo o nível do fluido estando OK e a válvula termostática já ter sido trocada.', '<b>Diagnóstico para seu Toyota Yaris (2021) Cinza 🚗💨</b>

É uma situação chatinha, mas vamos analisar! O fato de ser em subida e com ar condicionado ligado indica sobrecarga no sistema de arrefecimento.

<b>1. Possíveis Causas do Problema:</b>
*   <b>Ventoinha do Radiador</b> 🌬️: Pode não estar armando na velocidade correta (principalmente a mais alta) quando o AC está ligado ou o motor esquenta muito. É um clássico!
*   <b>Radiador Obstruído</b> 🧼: Mesmo sendo novo, pode haver sujeira externa nas aletas (folhas, insetos) ou, internamente, alguma obstrução parcial que impede a troca de calor eficiente sob carga.
*   <b>Tampa do Radiador/Reservatório</b> 💨: Se não veda corretamente, o sistema perde pressão e o fluido ferve antes, diminuindo a eficiência do arrefecimento.
*   <b>Bomba D''água</b> 💧: Embora o carro seja novo, uma bomba com problemas internos pode não circular o fluido adequadamente sob alta demanda.
*   <b>Ar no Sistema</b> 💭: Bolhas de ar podem criar "bolsões" quentes, impedindo a circulação eficaz do fluido mesmo com o nível correto.

<b>2. Passos Recomendados para Solucionar:</b>
*   <b>Verificar Ventoinha</b> 👀: Confirmar se ela liga em todas as velocidades (especialmente a mais alta) com o AC ligado e o motor aquecido.
*   <b>Inspeção e Limpeza do Radiador</b> ✨: Limpar as aletas externas (com cuidado!) e verificar se há danos ou pontos muito sujos que impedem o fluxo de ar.
*   <b>Teste da Tampa</b> 🧪: A tampa do radiador ou reservatório de expansão pode ser testada para ver se está mantendo a pressão correta do sistema.
*   <b>Desaerar o Sistema</b> 🌬️: Purgar o sistema de arrefecimento para remover qualquer bolha de ar que possa estar presa.

<b>3. Sugestões de Manutenção Preventiva:</b>
*   <b>Fluido de Arrefecimento</b> ✅: Usar sempre o fluido especificado pelo fabricante (concentrado + água desmineralizada) e no nível correto.
*   <b>Limpeza Periódica</b> 🚿: Limpar externamente o radiador de tempos em tempos para evitar acúmulo de sujeira e otimizar o fluxo de ar.
*   <b>Fique de Olho</b> 🧐: Monitore o ponteiro de temperatura (se houver) e qualquer luz no painel, especialmente em condições de alta demanda.

<b>4. Necessidade de Mecânico Profissional:</b>
*   <b>SIM, é essencial!</b> 👨‍🔧 Superaquecimento pode causar danos graves e caros ao motor. Um profissional tem equipamentos para testar pressão, fluxo, diagnosticar eletronicamente a ventoinha, sensores e verificar a bomba d''água. Leve o veículo o quanto antes para um diagnóstico preciso e seguro! 🚨', '2026-03-16', False, NULL) ON CONFLICT ("id") DO NOTHING;

INSERT INTO public."manutencoes" ("id", "data", "veiculo_id", "km", "observacao", "status", "custo", "imagem", "imagemNotaServico") VALUES (1, '2025-11-20', 1, 38045, NULL, 'Finalizada', 40.0, 'AgACAgEAAxkBAAIMoGk26zlptMi2vF6MWi-YzZfoa6BAAAINC2sbVvu4RVGJbw5kzDyjAQADAgADeQADNgQ.jpg', NULL) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."manutencoes" ("id", "data", "veiculo_id", "km", "observacao", "status", "custo", "imagem", "imagemNotaServico") VALUES (2, '2025-12-20', 1, 38787, NULL, 'Finalizada', 40.0, 'AgACAgEAAxkBAAIFuWlGxNIbcSIRapqnAyEBhAzeBqw4AAIHC2sb2ic5Ro4hSyW-I4J1AQADAgADeQADNgQ.jpg', NULL) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."manutencoes" ("id", "data", "veiculo_id", "km", "observacao", "status", "custo", "imagem", "imagemNotaServico") VALUES (9, '2026-02-04', 1, 40035, 'Oficina Digno Moto Peças', 'Finalizada', 372.0, 'AgACAgEAAxkBAAIR1WmCm5EQoQclIzEd56BRQtdfr1RXAAK3C2sb7nEZRJFmJ4KalQ18AQADAgADeQADOAQ.jpg', 'AgACAgEAAxkBAAIR_2mCozZSybmfY3e_K1dl-NZVLQmrAAK5C2sb7nEZRFDiBtEcIDr3AQADAgADeQADOAQ.jpg') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."manutencoes" ("id", "data", "veiculo_id", "km", "observacao", "status", "custo", "imagem", "imagemNotaServico") VALUES (7, '2025-02-11', 1, 0, 'Não tem registro da quilometragem nem a foto do painel na época', 'Finalizada', 580.0, 'images', 'AgACAgEAAxkBAAIQwWl4C3CgUXaANEZcLtxBYIrV7ZpEAALCC2sbk1DAR-17vEqyzwMZAQADAgADeQADOAQ.jpg') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."manutencoes" ("id", "data", "veiculo_id", "km", "observacao", "status", "custo", "imagem", "imagemNotaServico") VALUES (10, '2026-03-16', 1, 41618, NULL, 'Finalizada', 40.0, 'AgACAgEAAxkBAAITqWm5Q96TFNdNXri7Cae8_0j3kQH-AAKaC2sbLLjJRYPlPmdZ73NhAQADAgADeQADOgQ.jpg', NULL) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."manutencoes" ("id", "data", "veiculo_id", "km", "observacao", "status", "custo", "imagem", "imagemNotaServico") VALUES (11, '2026-05-01', 1, 43508, NULL, 'Finalizada', 42.0, 'AgACAgEAAxkBAAIUc2oB1f3uWreroDtv-d3o4_B6eis6AAIGDGsbKq4QRCcT4Pnjua0uAQADAgADeQADOwQ.jpg', NULL) ON CONFLICT ("id") DO NOTHING;

INSERT INTO public."manutencaoservicos" ("id", "manutencao_id", "servico_id") VALUES (1, 1, 1) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."manutencaoservicos" ("id", "manutencao_id", "servico_id") VALUES (2, 2, 1) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."manutencaoservicos" ("id", "manutencao_id", "servico_id") VALUES (6, 7, 3) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."manutencaoservicos" ("id", "manutencao_id", "servico_id") VALUES (8, 9, 3) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."manutencaoservicos" ("id", "manutencao_id", "servico_id") VALUES (9, 10, 1) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."manutencaoservicos" ("id", "manutencao_id", "servico_id") VALUES (10, 11, 1) ON CONFLICT ("id") DO NOTHING;

INSERT INTO public."manutencaoprodutos" ("id", "manutencao_id", "produto_id") VALUES (7, 9, 6) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."manutencaoprodutos" ("id", "manutencao_id", "produto_id") VALUES (8, 9, 2) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."manutencaoprodutos" ("id", "manutencao_id", "produto_id") VALUES (9, 9, 3) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."manutencaoprodutos" ("id", "manutencao_id", "produto_id") VALUES (10, 9, 8) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."manutencaoprodutos" ("id", "manutencao_id", "produto_id") VALUES (11, 9, 1) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."manutencaoprodutos" ("id", "manutencao_id", "produto_id") VALUES (12, 9, 9) ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."manutencaoprodutos" ("id", "manutencao_id", "produto_id") VALUES (13, 11, 1) ON CONFLICT ("id") DO NOTHING;

INSERT INTO public."notificacoes" ("id", "dataNotificacao", "tipoNotificacao", "usuario_id", "servico_id", "manutencao_id", "veiculo_id", "titulo", "conteudo", "status") VALUES (1, '2026-01-02', 'ProximaManutencao', 1, NULL, 2, 1, 'Próxima Manutenção', 'Olá, Pedro Paulo! A data da próxima manutenção do seu veículo Honda Bros 160 Vermelha - 2022 (RGH6F20) é: 20/01/2026.', 'Enviada') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."notificacoes" ("id", "dataNotificacao", "tipoNotificacao", "usuario_id", "servico_id", "manutencao_id", "veiculo_id", "titulo", "conteudo", "status") VALUES (2, '2026-01-03', 'ProximaManutencao', 1, NULL, 2, 1, 'Próxima Manutenção', 'Olá, Pedro Paulo! A data da próxima manutenção do seu veículo Honda Bros 160 Vermelha - 2022 (RGH6F20) é: 20/01/2026.', 'Enviada') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."notificacoes" ("id", "dataNotificacao", "tipoNotificacao", "usuario_id", "servico_id", "manutencao_id", "veiculo_id", "titulo", "conteudo", "status") VALUES (3, '2026-01-10', 'ProximaManutencao', 1, NULL, 2, 1, 'Próxima Manutenção', 'Olá, Pedro Paulo! A data da próxima manutenção do seu veículo Honda Bros 160 Vermelha - 2022 (RGH6F20) é: 20/01/2026.', 'Enviada') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."notificacoes" ("id", "dataNotificacao", "tipoNotificacao", "usuario_id", "servico_id", "manutencao_id", "veiculo_id", "titulo", "conteudo", "status") VALUES (4, '2026-01-11', 'ProximaManutencao', 1, NULL, 2, 1, 'Próxima Manutenção', 'Olá, Pedro Paulo! A data da próxima manutenção do seu veículo Honda Bros 160 Vermelha - 2022 (RGH6F20) é: 20/01/2026.', 'Enviada') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."notificacoes" ("id", "dataNotificacao", "tipoNotificacao", "usuario_id", "servico_id", "manutencao_id", "veiculo_id", "titulo", "conteudo", "status") VALUES (5, '2026-01-12', 'ProximaManutencao', 1, NULL, 2, 1, 'Próxima Manutenção', 'Olá, Pedro Paulo! A data da próxima manutenção do seu veículo Honda Bros 160 Vermelha - 2022 (RGH6F20) é: 20/01/2026.', 'Enviada') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."notificacoes" ("id", "dataNotificacao", "tipoNotificacao", "usuario_id", "servico_id", "manutencao_id", "veiculo_id", "titulo", "conteudo", "status") VALUES (6, '2026-01-13', 'ProximaManutencao', 1, NULL, 2, 1, 'Próxima Manutenção', 'Olá, Pedro Paulo! A data da próxima manutenção do seu veículo Honda Bros 160 Vermelha - 2022 (RGH6F20) é: 20/01/2026.', 'Enviada') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."notificacoes" ("id", "dataNotificacao", "tipoNotificacao", "usuario_id", "servico_id", "manutencao_id", "veiculo_id", "titulo", "conteudo", "status") VALUES (7, '2026-01-14', 'ProximaManutencao', 1, NULL, 2, 1, 'Próxima Manutenção', 'Olá, Pedro Paulo! A data da próxima manutenção do seu veículo Honda Bros 160 Vermelha - 2022 (RGH6F20) é: 20/01/2026.', 'Enviada') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."notificacoes" ("id", "dataNotificacao", "tipoNotificacao", "usuario_id", "servico_id", "manutencao_id", "veiculo_id", "titulo", "conteudo", "status") VALUES (8, '2026-01-15', 'ProximaManutencao', 1, NULL, 2, 1, 'Próxima Manutenção', 'Olá, Pedro Paulo! A data da próxima manutenção do seu veículo Honda Bros 160 Vermelha - 2022 (RGH6F20) é: 20/01/2026.', 'Enviada') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."notificacoes" ("id", "dataNotificacao", "tipoNotificacao", "usuario_id", "servico_id", "manutencao_id", "veiculo_id", "titulo", "conteudo", "status") VALUES (9, '2026-01-16', 'ProximaManutencao', 1, NULL, 2, 1, 'Próxima Manutenção', 'Olá, Pedro Paulo! A data da próxima manutenção do seu veículo Honda Bros 160 Vermelha - 2022 (RGH6F20) é: 20/01/2026.', 'Enviada') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."notificacoes" ("id", "dataNotificacao", "tipoNotificacao", "usuario_id", "servico_id", "manutencao_id", "veiculo_id", "titulo", "conteudo", "status") VALUES (10, '2026-01-17', 'ProximaManutencao', 1, NULL, 2, 1, 'Próxima Manutenção', 'Olá, Pedro Paulo! A data da próxima manutenção do seu veículo Honda Bros 160 Vermelha - 2022 (RGH6F20) é: 20/01/2026.', 'Enviada') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."notificacoes" ("id", "dataNotificacao", "tipoNotificacao", "usuario_id", "servico_id", "manutencao_id", "veiculo_id", "titulo", "conteudo", "status") VALUES (11, '2026-01-18', 'ProximaManutencao', 1, NULL, 2, 1, 'Próxima Manutenção', 'Olá, Pedro Paulo! A data da próxima manutenção do seu veículo Honda Bros 160 Vermelha - 2022 (RGH6F20) é: 20/01/2026.', 'Enviada') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."notificacoes" ("id", "dataNotificacao", "tipoNotificacao", "usuario_id", "servico_id", "manutencao_id", "veiculo_id", "titulo", "conteudo", "status") VALUES (44, '2026-01-19', 'ProximaManutencao', 1, NULL, 2, 1, 'Próxima Manutenção', 'Olá, Pedro Paulo! A data da próxima manutenção do seu veículo Honda Bros 160 Vermelha - 2022 (RGH6F20) é: 20/01/2026.', 'Enviada') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."notificacoes" ("id", "dataNotificacao", "tipoNotificacao", "usuario_id", "servico_id", "manutencao_id", "veiculo_id", "titulo", "conteudo", "status") VALUES (45, '2026-02-22', 'ProximaManutencao', 1, NULL, 9, 1, 'Próxima Manutenção', 'Olá, Pedro Paulo! A data da próxima manutenção do seu veículo Honda Bros 160 Vermelha - 2022 (RGH6F20) é: 04/03/2026.', 'Enviada') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."notificacoes" ("id", "dataNotificacao", "tipoNotificacao", "usuario_id", "servico_id", "manutencao_id", "veiculo_id", "titulo", "conteudo", "status") VALUES (46, '2026-02-23', 'ProximaManutencao', 1, NULL, 9, 1, 'Próxima Manutenção', 'Olá, Pedro Paulo! A data da próxima manutenção do seu veículo Honda Bros 160 Vermelha - 2022 (RGH6F20) é: 04/03/2026.', 'Enviada') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."notificacoes" ("id", "dataNotificacao", "tipoNotificacao", "usuario_id", "servico_id", "manutencao_id", "veiculo_id", "titulo", "conteudo", "status") VALUES (47, '2026-02-24', 'ProximaManutencao', 1, NULL, 9, 1, 'Próxima Manutenção', 'Olá, Pedro Paulo! A data da próxima manutenção do seu veículo Honda Bros 160 Vermelha - 2022 (RGH6F20) é: 04/03/2026.', 'Enviada') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."notificacoes" ("id", "dataNotificacao", "tipoNotificacao", "usuario_id", "servico_id", "manutencao_id", "veiculo_id", "titulo", "conteudo", "status") VALUES (48, '2026-02-25', 'ProximaManutencao', 1, NULL, 9, 1, 'Próxima Manutenção', 'Olá, Pedro Paulo! A data da próxima manutenção do seu veículo Honda Bros 160 Vermelha - 2022 (RGH6F20) é: 04/03/2026.', 'Enviada') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."notificacoes" ("id", "dataNotificacao", "tipoNotificacao", "usuario_id", "servico_id", "manutencao_id", "veiculo_id", "titulo", "conteudo", "status") VALUES (49, '2026-02-26', 'ProximaManutencao', 1, NULL, 9, 1, 'Próxima Manutenção', 'Olá, Pedro Paulo! A data da próxima manutenção do seu veículo Honda Bros 160 Vermelha - 2022 (RGH6F20) é: 04/03/2026.', 'Enviada') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."notificacoes" ("id", "dataNotificacao", "tipoNotificacao", "usuario_id", "servico_id", "manutencao_id", "veiculo_id", "titulo", "conteudo", "status") VALUES (50, '2026-02-27', 'ProximaManutencao', 1, NULL, 9, 1, 'Próxima Manutenção', 'Olá, Pedro Paulo! A data da próxima manutenção do seu veículo Honda Bros 160 Vermelha - 2022 (RGH6F20) é: 04/03/2026.', 'Enviada') ON CONFLICT ("id") DO NOTHING;
INSERT INTO public."notificacoes" ("id", "dataNotificacao", "tipoNotificacao", "usuario_id", "servico_id", "manutencao_id", "veiculo_id", "titulo", "conteudo", "status") VALUES (51, '2026-02-28', 'ProximaManutencao', 1, NULL, 9, 1, 'Próxima Manutenção', 'Olá, Pedro Paulo! A data da próxima manutenção do seu veículo Honda Bros 160 Vermelha - 2022 (RGH6F20) é: 04/03/2026.', 'Enviada') ON CONFLICT ("id") DO NOTHING;

SET session_replication_role = 'origin';
