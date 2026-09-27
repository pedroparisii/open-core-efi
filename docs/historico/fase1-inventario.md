# Fase 1 — Inventário de hardware

Fonte: `inventory/inventario-20260927-0257.json` (gerado por `tools/inventario.ps1`, sem privilégio de Administrador).
Itens marcados **[F2]** serão confirmados na Fase 2 (pesquisa de compatibilidade).

## Sistema

| Item | Valor |
|---|---|
| Windows | Windows 11 Pro 25H2, build 26200.7171 |
| Modo de boot | UEFI |
| Secure Boot | Ativado (registro `UEFISecureBootEnabled = 1`) |
| CSM | Não lido diretamente; com Secure Boot ativo, o CSM está necessariamente desligado |
| VBS / Memory Integrity | Em execução (status 2) — afeta só o Windows |
| Fast Startup | Desligado |
| Relógio (RealTimeIsUniversal) | Não definido → Windows usa hora local; macOS usa UTC (diferença de horário no dual boot) |

## Placa-mãe / firmware

| Item | Valor |
|---|---|
| Placa | ASUSTeK PRIME H410M-E, Rev 1.xx |
| BIOS | AMI, versão **1620** (07/2021), SMBIOS 3.2 |
| Chipset | Intel 400-series PCH-V (H410): LPC `8086:A3DA`, SMBus `A3A3`, PMC `A3A1`, HECI `A3BA` |

## CPU

| Item | Valor |
|---|---|
| Modelo | Intel Core i5-10400F, 6C/12T |
| CPUID | `0xA0653` (família 6, modelo 165 = Comet Lake-S) |
| iGPU | **Nenhuma** (sufixo F) — a RX 6600 é a única saída de vídeo |
| Objetos ACPI | `\_SB.PR00` … `\_SB.PR11` — `Processor` legados sob `\_SB` (confirmado no DSDT, Fase 2) |

## RAM

2× Kingston FURY `KF2666C16D4/8G`, 8 GB cada, 2666 MHz, dual channel (ChannelA-DIMM1 / ChannelB-DIMM1).

## GPU

| Item | Valor |
|---|---|
| Placa | AMD Radeon RX 6600 (Navi 23) |
| PCI ID | `1002:73FF`, subsystem `148C:2413` (fabricante PowerColor) |
| Caminho | `PciRoot(0x0)/Pci(0x1,0x0)/Pci(0x0,0x0)/Pci(0x0,0x0)/Pci(0x0,0x0)` (PEG0 → switch AMD upstream/downstream → GPU) |
| Áudio HDMI/DP | `1002:AB28`, codec `1002:AA01` |

## Áudio onboard

| Item | Valor |
|---|---|
| Controlador | Intel HDA `8086:A3F0` em `\_SB.PCI0.HDAS` (`Pci(0x1F,0x3)`) |
| Codec | **Realtek ALC887** (`10EC:0887`, subsystem `1043:86C7`) |

## Ethernet

| Item | Valor |
|---|---|
| Chip | **Realtek RTL8111** (`10EC:8168`, rev 15 → família RTL8111H) |
| Caminho | `\_SB.PCI0.RP08.PXSX` (`Pci(0x1C,0x7)/Pci(0x0,0x0)`) |

## USB

| Item | Valor |
|---|---|
| Controlador | **Um único** xHCI Intel `8086:A3AF` em `\_SB.PCI0.XHC` (`Pci(0x14,0x0)`) |
| Dispositivos atuais | teclado/mouse/receptores HID (VID 1EA7, 258A, 291D) e o dongle 368B:8D81 nas portas 3–6 do hub raiz |

O mapeamento de portas (limite de 15 portas no macOS) só pode ser feito testando cada porta física. **[F2]** Suporte nativo do xHCI `A3AF` do PCH-V.

## Wi-Fi / Bluetooth — `VID_368B&PID_8D81`

É um **dongle USB AICSemi AIC8800D80** (Wi-Fi + Bluetooth combo). O Windows reconhece o Wi-Fi como "AIC8800D80 USB WiFi" (desconectado) e o Bluetooth como "Generic Bluetooth Adapter".
Não há driver oficial para macOS. **[F2]** Confirmar se existe algum suporte; a proposta é **não** incluir kext e deixá-lo sem uso no macOS.

## Armazenamento

| Disco (Windows) | Modelo | Barramento | Partições | Papel atual |
|---|---|---|---|---|
| 0 | Kingston A400 `SA400S37120G` (fw 03090005) | SATA | MSR + NTFS **D:** (111,77 GB) | dados |
| 1 | Kingston A400 `SA400S37120G` (fw 03070009) | SATA | **ESP 100 MB** + MSR + NTFS **E:** (111,67 GB) | **contém o carregador de boot do Windows** (`IsSystem = true`) |
| 2 | Kingston NV2 `SNV2S500G` (fw SBN00100) | NVMe, controlador `2646:5017`, `\_SB.PCI0.RP11.PXSX` | MSR + **C:** (Windows) + Recovery | Windows (`IsBoot = true`), **sem ESP** |

Controlador SATA: Intel AHCI `8086:A382` (`\_SB.PCI0.SAT0`) — modo AHCI (não RAID/Optane).

## ACPI relevante (lista de dispositivos PnP do Windows)

- `\_SB.AWAC` presente (ACPI000E): relógio AWAC da série 300/400 → no macOS precisa do RTC legado. **[F4]**
- Nenhum Embedded Controller ativo: o DSDT tem `\_SB.PCI0.LPCB.H_EC` (PNP0C09) com `_STA` = 0 → macOS precisa de um EC falso (`SSDT-EC`). **[F4]**
- CPUs em `\_SB.PR00`…: relevante para o `SSDT-PLUG`. **[F4]**
- `\_SB.PCI0.LPCB` (LPC), `\_SB.PCI0.PPMC` (PMC), `\_SB.PCI0.SBUS` (SMBus), `\_SB.PCI0.LPCB.HPET`.
- Super I/O em `\_SB.PCI0.LPCB.SIO1`. **[F2]** Identificar o chip (possivelmente Nuvoton/ITE) para o SMCSuperIO.

## Achados críticos

1. **O Windows depende do disco SATA 1 (E:) para dar boot.** A ESP com o Boot Manager está nele, não no NV2. Apagar esse disco deixa o Windows sem boot, mesmo com o NV2 intacto.
2. **Nenhum dos alvos citados é seguro sem mudança de plano:**
   - NV2 (C:) → é o Windows.
   - A400 "E:" (disco 1) → é o boot do Windows.
   - Alvo seguro: **A400 "D:" (disco 0)**, que só tem dados. Precisa confirmar que pode ser apagado.
3. Os dois A400 são do **mesmo modelo e tamanho**. No Utilitário de Disco do instalador, vão se diferenciar só pelas partições (disco 0: sem ESP; disco 1: com ESP de 100 MB).

## Informações ainda faltando

| Item | Como obter | Obrigatório? |
|---|---|---|
| Tabelas ACPI (DSDT/SSDTs) | ✅ Feito com SSDTTime (sem admin), em `acpi/` (fora do git) | **Sim** (Fase 4) |
| Confirmação do Secure Boot + `bcdedit` | Rodar `inventario.ps1` como Administrador | Opcional |
| Estado de CFG Lock | Ferramenta `ControlMsrE2` do OpenCore (só leitura) | Sim, antes do 1º boot |
| Opções da BIOS 1620 (Above 4G, ReBAR, VT-d, CSM, Serial Port, etc.) | Fotos das telas da BIOS | Sim (Fase 9) |
| BIOS mais recente para a placa | ✅ 1806 (2026-01-13); usuário mantém 1620 | Recomendado |
| Conteúdo do disco 0 (D:) pode ser apagado? | ✅ Confirmado pelo usuário | **Sim** |
| Chip Super I/O | HWiNFO (seção Motherboard) ou DSDT | Opcional (sensores) |
| Conexão do monitor (HDMI ou DP) | ✅ DisplayPort | Útil para debug |
