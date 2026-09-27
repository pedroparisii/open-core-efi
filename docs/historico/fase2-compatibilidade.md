# Fase 2 — Compatibilidade e decisões

Fontes: Dortania (Comet Lake, Tahoe, SMBIOS support, Kexts), `Configuration.pdf` 1.0.7, READMEs/changelogs das kexts, dump ACPI desta placa (`acpi/`, fora do git).

## Correções ao inventário da Fase 1
- CPUs: o DSDT declara `Processor (PR00..)` **legados** em `\_SB` (não `Device`). SSDT-PLUG padrão serve.
- EC: o DSDT tem `\_SB.PCI0.LPCB.H_EC` (PNP0C09), mas `_STA` retorna sempre 0 — por isso o Windows não lista. macOS precisa de EC falso.

## Versão do macOS: **Sequoia 15** (decisão do usuário)
| | Sequoia 15 | Tahoe 26 |
|---|---|---|
| Áudio analógico ALC887 | AppleALC OK | AppleHDA removido do sistema → VoodooHDA ou root patch (Dortania, página Tahoe) |
| WhateverGreen + AMD | OK | Dortania: problema de connector patching AMD no 26, sem correção; WEG 1.7.0 ainda é o último |
| MacPro7,1 | Suportado | Suportado |

A EFI usa MacPro7,1, então dá para migrar para o Tahoe depois sem trocar SMBIOS (exigiria rever áudio e WEG).

## SMBIOS: **MacPro7,1**
- Dortania: CPU sem iGPU **deve** evitar iMac (Quick Look/DRM quebram); opções são iMacPro1,1 e MacPro7,1.
- iMacPro1,1 não é suportado no Tahoe → MacPro7,1 mantém o caminho de atualização.
- Custo: RestrictEvents para esconder avisos de PCI/RAM; possível ajuste de gerenciamento de energia/sleep depois (Dortania, "Fixing Power Management").
- `UpdateSMBIOSMode=Custom` + `CustomSMBIOSGuid`: SMBIOS só para o macOS (Configuration.pdf: evita colisão com ativação do Windows).

## Itens verificados
| Item | Resultado | Ação |
|---|---|---|
| i5-10400F (Comet Lake-S, `0xA0653`) | Suportado nativamente (Catalina 10.15.4+) | Sem emulação de CPUID |
| RX 6600 `1002:73FF` (Navi 23) | Nativo desde 12.1 | WhateverGreen + `agdpmod=pikera` (Dortania: Navi) |
| RTL8111H `10EC:8168` | RealtekRTL8111 3.0.0: min 10.15, changelog cita Tahoe | Kext incluída |
| ALC887 `10EC:0887` sub `1043:86C7` | AppleALC tem layouts 1,2,3,5,7,11,12,13,17,18,20,33,40,50,52,53,87,99; nenhum da H410M-E | Começar com **layout-id 3** (3 conectores + frontal); alternativas 5, 1, 11, 7 |
| xHCI `8086:A3AF` (PCH-V) | Dortania não lista o H410 explicitamente. Os IDs do PCH-V espelham o PCH série 200 (SATA A382↔A282, HDA A3F0↔A2F0, SMBus A3A3↔A2A3) | `device-id` falso **A2AF** (nativo) via DeviceProperties. **Hipótese:** se o USB falhar, remover essa entrada é o 1º teste |
| Portas USB | 26 portas no ACPI (HS01–14, USR1–2, SS01–10) > limite de 15 | No instalador funcionam as 15 primeiras (USB 2.0); mapear com USBToolBox no pós-instalação |
| AWAC | RTC só ativo com `STAS==1` | SSDT-RTCAWAC (`STAS=1` no Darwin) |
| DMAR | Tem 1 Reserved Memory Region | `DisableIoMapper=YES` (README do RTL8111: AppleVTD desligado na dúvida) |
| CFG Lock | Não dá para ler no Windows | `AppleXcpmCfgLock=YES`; conferir com `ControlMsrE2.efi` no 1º boot |
| NVMe Kingston NV2 | Visível no macOS (Windows) | NVMeFix para gerenciamento de energia |
| Wi-Fi/BT AIC8800D80 | Sem driver para macOS | Ignorado (sem kext) |
| Super I/O | Não identificado (HID PNP0C02 genérico) | SMCSuperIO detecta sozinho; se não, só perde leitura de ventoinhas |
| BIOS | Atual 1620; mais recente **1806** (2026-01-13) | Usuário optou por manter a 1620 |
