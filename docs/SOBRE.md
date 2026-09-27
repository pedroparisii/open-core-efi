# Sobre o projeto

Uma EFI OpenCore montada do zero para um único PC, com dual boot macOS + Windows. A regra desde o início foi: **nada de EFI pronta de terceiros**. Cada SSDT, kext e opção do `config.plist` foi escolhido a partir do hardware desta máquina e justificado pela documentação oficial (guia Dortania, `Configuration.pdf` do OpenCore e READMEs das kexts).

## Hardware

| Componente | Modelo | IDs |
|---|---|---|
| CPU | Intel Core i5-10400F — Comet Lake-S, 6C/12T, **sem iGPU** | CPUID `0xA0653` |
| Placa-mãe | ASUS PRIME H410M-E, chipset H410 (PCH-V), BIOS 1620 | |
| GPU | PowerColor Radeon RX 6600 (Navi 23) | `1002:73FF` |
| Áudio | Realtek ALC887 | `10EC:0887` |
| Ethernet | Realtek RTL8111H | `10EC:8168` |
| USB | Controlador xHCI Intel único | `8086:A3AF` |
| RAM | 2× 8 GB DDR4-2666 | |
| Wi-Fi/BT | Dongle USB AIC8800D80 — **sem suporte no macOS**, não usado | `368B:8D81` |

## Principais decisões

**macOS Sequoia 15, não Tahoe 26.** O Tahoe é o último macOS para Intel, mas removeu o `AppleHDA` (o AppleALC deixa de funcionar e o áudio analógico precisaria de VoodooHDA com SIP reduzido) e tem um problema conhecido do WhateverGreen com GPUs AMD. No Sequoia tudo funciona com kexts oficiais e SIP ligado.

**SMBIOS MacPro7,1.** CPUs sem iGPU não devem usar SMBIOS de iMac (o macOS espera uma iGPU para Quick Look/DRM). Entre iMacPro1,1 e MacPro7,1, só o MacPro7,1 continua suportado no Tahoe, o que mantém o caminho de atualização aberto. O `RestrictEvents` esconde os avisos de PCI/RAM típicos desse modelo. O SMBIOS é aplicado **só ao macOS** (`UpdateSMBIOSMode=Custom` + `CustomSMBIOSGuid`), então o Windows continua vendo a placa real.

**SSDTs mínimos, gerados pelo SSDTTime a partir do DSDT desta placa:**
| SSDT | Motivo encontrado no DSDT |
|---|---|
| SSDT-PLUG | CPUs declaradas como `Processor` em `\_SB.PR00…` |
| SSDT-EC | Existe um `H_EC`, mas seu `_STA` sempre retorna 0; o macOS precisa de um EC |
| SSDT-USBX | Propriedades de energia USB para SMBIOS Skylake+ |
| SSDT-RTCAWAC | O RTC legado só liga quando `STAS=1`; o AWAC da série 400 não funciona no macOS |
| SSDT-USB-Reset | Recomendado pela Dortania para placas ASUS série 400 |

**USB.** O xHCI `A3AF` do chipset H410 não está documentado pela Dortania. Os IDs do PCH-V espelham exatamente os do chipset série 200 (`A382`↔`A282`, `A3F0`↔`A2F0`, `A3AF`↔`A2AF`), então o controlador é apresentado ao macOS como `A2AF`, que é nativo. Funcionou na primeira tentativa.

**Kexts (só o necessário):** Lilu, VirtualSMC (+SMCProcessor, SMCSuperIO), WhateverGreen, AppleALC (layout-id 3), RestrictEvents, NVMeFix e RealtekRTL8111.

## Arquitetura do dual boot

```
NVMe 500 GB   → Windows 11 (C:) + EFI do Windows + Recovery do Windows
SSD 120 GB #1 → macOS Sequoia (APFS) + EFI com o OpenCore  ← 1º na ordem de boot
SSD 120 GB #2 → "E:" em exFAT, compartilhado entre os dois sistemas
```

Ao ligar, a BIOS carrega o OpenCore, que mostra o menu gráfico (tema GoldenGate) com macOS e Windows. Cada sistema tem o próprio carregador no próprio disco: o Windows inicia normalmente mesmo sem os SSDs do macOS.

O Windows usa **BitLocker** (TPM, PCRs 0/2/4/11). Por isso ele é sempre iniciado pelo menu do OpenCore: o TPM grava essa sequência de boot, e iniciar por outro caminho faz o Windows pedir a chave de recuperação.

## Problemas encontrados e soluções

| Problema | Causa | Solução |
|---|---|---|
| BIOS em "safe mode" ao reiniciar pelo macOS | macOS escrevendo em área do CMOS que a placa não aceita | `DisableRtcChecksum` |
| Windows pedindo chave do BitLocker | Mudanças no Secure Boot e na sequência de boot alteram as medições do TPM | Suspender o BitLocker antes de cada mudança; o Windows regrava as medições no boot seguinte |
| Windows Hello pedindo novo PIN | Container do PIN preso ao estado anterior do Secure Boot | Recriar o PIN depois que o Secure Boot ficou estável |
| Windows dependia de outro SSD para iniciar | EFI do Windows estava no SSD de 120 GB | EFI nova criada no NVMe com `bcdboot`; Recovery registrado de novo |
| Relógio 3 h adiantado no Windows após usar o macOS | macOS grava UTC no relógio da placa, Windows lê como hora local | `RealTimeIsUniversal = 1` no Windows |

## Como foi feito
1. Inventário do hardware no Windows (somente leitura) e dump das tabelas ACPI.
2. Pesquisa de compatibilidade e escolha da versão do macOS e do SMBIOS.
3. Download das versões mais recentes nos repositórios oficiais ([versoes.md](versoes.md)).
4. SSDTs, kexts e `config.plist` gerado por script ([tools/build_config.py](../tools/build_config.py)), validado com `ocvalidate`.
5. Configuração da BIOS, instalador USB com `macrecovery.py`, instalação.
6. Pós-instalação: correções acima, menu gráfico e OpenCore movido do pendrive para o disco.

Os detalhes de cada fase estão em [docs/historico/](historico/).

## Pendências
- Mapeamento USB (limite de 15 portas no macOS) com o USBToolBox.
- Testar o áudio pelas saídas P2 (layout-id 3; alternativas 5, 1, 11, 7).
- Confirmar o CFG Lock com `ControlMsrE2` e, se destravado, desligar `AppleXcpmCfgLock`.

## Créditos e licenças

| Projeto | Uso | Licença |
|---|---|---|
| [OpenCorePkg](https://github.com/acidanthera/OpenCorePkg) | Bootloader, drivers, ferramentas | BSD-3-Clause |
| [OcBinaryData](https://github.com/acidanthera/OcBinaryData) | Ícones e fontes do OpenCanopy | Sem arquivo de licença no repositório; recursos publicados pela acidanthera para uso com o OpenCore |
| [Lilu](https://github.com/acidanthera/Lilu), [VirtualSMC](https://github.com/acidanthera/VirtualSMC), [WhateverGreen](https://github.com/acidanthera/WhateverGreen), [AppleALC](https://github.com/acidanthera/AppleALC), [RestrictEvents](https://github.com/acidanthera/RestrictEvents), [NVMeFix](https://github.com/acidanthera/NVMeFix) | Kexts | BSD-3-Clause |
| [RealtekRTL8111](https://github.com/Mieze/RTL8111_driver_for_OS_X) | Kext de Ethernet | GPL-2.0 — código-fonte no repositório original |
| [SSDTTime](https://github.com/corpnewt/SSDTTime), [GenSMBIOS](https://github.com/corpnewt/GenSMBIOS) | Geração dos SSDTs e do SMBIOS | MIT |
| [Dortania](https://dortania.github.io/OpenCore-Install-Guide/) | Guia de referência | — |

Os binários em `EFI/` são redistribuídos sem modificação a partir das releases oficiais listadas em [versoes.md](versoes.md). Os textos das licenças (avisos de copyright exigidos pela BSD-3 e a GPL-2.0) estão em [docs/licencas/](licencas/).
