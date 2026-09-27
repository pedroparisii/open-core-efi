
Quero montar uma EFI OpenCore específica para este PC para dual boot macOS + Windows. Já fizemos a Fase 1 (inventário) em outra sessão; leia `docs/fase1-inventario.md` e `inventory/*.json` antes de tudo.

**Regras**
- Nada de EFI pronta de terceiros. Pode consultar como referência, mas cada escolha tem que ser justificada pelo *meu* hardware e pela documentação oficial (Dortania, `Configuration.pdf` do OpenCorePkg, READMEs das kexts).
- Baixe sempre as versões mais recentes dos repositórios oficiais (acidanthera, OpenIntelWireless, corpnewt, etc.) e anote as versões usadas.
- Não invente compatibilidade. Se algo for incerto, explique e proponha uma alternativa. Se houver incompatibilidade crítica, pare e me pergunte.
- Explique em 1–2 frases o motivo antes de cada etapa importante. Sem textão.
- Não publique serial, MLB, UUID nem ROM em arquivos commitados (`config.plist` com SMBIOS real fica fora do git ou com placeholders).

**Segurança no Windows (obrigatório)**
- Comandos de leitura podem rodar livremente.
- **Nunca** formate, particione, monte a ESP, rode `bcdedit /set`, `diskpart`, `mountvol`, `Clear-Disk` nem altere a BIOS/NVRAM sem me mostrar o comando e eu aprovar.
- Disco 2 (NV2, C:) = Windows. Disco 1 (A400, E:) = **contém a ESP com o boot do Windows**. Nenhum dos dois pode ser tocado.
- Alvo do macOS: **Disco 0 (A400, D:)**, depois de eu confirmar que pode apagar.
- O pendrive do instalador é o disco F:, vc esta autorizado gravar nele.

**Hardware (resumo; detalhes no inventário)**
i5-10400F (Comet Lake, sem iGPU) · ASUS PRIME H410M-E, BIOS 1620 · RX 6600 PowerColor (`1002:73FF`) · ALC887 · RTL8111H (`10EC:8168`) · xHCI Intel `8086:A3AF` (único) · 2×8 GB DDR4-2666 · AWAC presente, sem EC · Wi-Fi/BT = dongle USB AIC8800D80 (`368B:8D81`), sem suporte no macOS → ignorar.

**Próximos passos**
1. Rodar `tools/inventario.ps1` como Administrador (Secure Boot/bcdedit) e fazer dump ACPI com SSDTTime.
2. Fase 2: compatibilidade e escolha da versão do macOS (Comet Lake + Navi 23, macOS 26 Tahoe é o último com Intel — comparar com Sequoia), SMBIOS, CFG Lock, BIOS mais recente, suporte ao xHCI `A3AF`, layout-id do ALC887, kext da RTL8111.
3. Fases 3–8: baixar ferramentas → SSDTs (só os necessários, via SSDTTime) → kexts mínimas → `config.plist` → SMBIOS com GenSMBIOS → `ocvalidate` da mesma versão do OpenCore (duas passadas).
4. Fase 9: me dizer as configurações da BIOS (Nome / Valor / Motivo), sem alterar nada.
5. Fase 10: instalador USB com `macrecovery.py` + EFI no pendrive.
6. Fase 11: checklist antes do primeiro boot + como abrir o boot menu da ASUS (F8).
7. Fases 12–13: debug (uma mudança por vez, OpenCore DEBUG se preciso) e pós-instalação (GPU, CPU, Ethernet, áudio, mapeamento USB, NVRAM, sleep, OpenCore no disco, backup da EFI, relógio UTC no dual boot).

**Entrega final**: caminho e árvore da EFI, SSDTs, kexts, drivers, versões (OpenCore/macOS), SMBIOS escolhido, configurações da BIOS, saída do ocvalidate, problemas conhecidos e próximos passos. Estrutura: `EFI/BOOT/BOOTx64.efi`, `EFI/OC/{ACPI,Drivers,Kexts,Resources,Tools,OpenCore.efi,config.plist}`.

Pendências minhas: confirmar que o disco D: pode ser apagado; informar se o monitor usa HDMI ou DisplayPort; fotos da BIOS quando pedido.


PODE ME PERGUNTAR OQ QUISER A HORA Q QUISER
