# Open Core EFI

EFI **OpenCore 1.0.7** feita do zero para meu PC em específico, em dual boot **macOS Sequoia 15 + Windows 11**.

| | |
|---|---|
| CPU | Intel Core i5-10400F |
| Placa-mãe | ASUS PRIME H410M-E (BIOS 1620) |
| GPU | AMD Radeon RX 6600 (Navi 23) |
| Rede / Áudio | Realtek RTL8111H / Realtek ALC887 |
| SMBIOS | MacPro7,1 |

## O que funciona
Aceleração da GPU, Ethernet, USB, áudio USB, NVRAM, atualizações do macOS pelo Ajustes do Sistema e boot pelo menu gráfico do OpenCore (sem pendrive), c  om o Windows (BitLocker ativo) iniciando pelo mesmo menu.

## Estrutura
```
EFI/                 EFI pronta (SMBIOS com placeholders)
tools/build_config.py  gera o config.plist a partir do Sample.plist oficial
tools/inventario.ps1   inventário de hardware (Windows, somente leitura)
inventory/           resultado do inventário
docs/SOBRE.md        o projeto explicado: decisões, arquitetura, créditos
docs/versoes.md      versões de tudo que foi usado
docs/ssdt/           fontes dos SSDTs
docs/historico/      registro de cada fase
CLAUDE.md            guia de manutenção
```

## Usar esta EFI
Ela foi feita para **este** hardware; use apenas se tiver o hardware identico ao meu.
1. Gere o seu SMBIOS MacPro7,1 com o [GenSMBIOS](https://github.com/corpnewt/GenSMBIOS) e preencha `PlatformInfo > Generic` no `EFI/OC/config.plist` (serial, MLB, UUID, ROM).
2. Valide com o `ocvalidate` da **mesma versão** do OpenCore (1.0.7).
3. Configure a BIOS conforme [docs/historico/fase9-bios.md](docs/historico/fase9-bios.md).

## Créditos
[OpenCorePkg](https://github.com/acidanthera/OpenCorePkg) e kexts da [acidanthera](https://github.com/acidanthera), [RealtekRTL8111](https://github.com/Mieze/RTL8111_driver_for_OS_X), ferramentas da [corpnewt](https://github.com/corpnewt) e o guia da [Dortania](https://dortania.github.io/OpenCore-Install-Guide/). Licenças em [docs/SOBRE.md](docs/SOBRE.md#créditos-e-licenças).
