# Guia de manutenção — EFI OpenCore (i5-10400F / RX 6600 / PRIME H410M-E)

Contexto para sessões futuras do Claude Code. O projeto está **concluído e em uso diário**; qualquer mudança é manutenção. Leia também `docs/SOBRE.md` (decisões) e `docs/versoes.md` (versões).

## Regras (definidas pelo dono do PC)
- Responder em português. Explicar em 1–2 frases o motivo antes de cada etapa importante; sem textão.
- Nada de EFI pronta de terceiros: toda escolha justificada pelo hardware + Dortania / `Configuration.pdf` / README das kexts. Não inventar compatibilidade; se for incerto, dizer e propor alternativa.
- Baixar sempre dos repositórios oficiais e registrar a versão em `docs/versoes.md`.
- **Nunca** commitar serial, MLB, UUID ou ROM (o ROM é o MAC da RTL8111). O `EFI/OC/config.plist` do git usa placeholders.
- Comandos de leitura: livres. **Sempre mostrar e esperar aprovação** antes de: `diskpart`, formatar/particionar, montar ESP, `mountvol`, `bcdedit /set`, `bcdboot`, `reagentc`, `manage-bde`, mudanças de BIOS/NVRAM.
- A sessão normalmente **não** roda como Administrador: comandos elevados são rodados pelo usuário, que cola a saída. Conferir cada saída antes do próximo passo.
- No PowerShell, `{bootmgr}` precisa de aspas: `bcdedit /enum '{bootmgr}'`.

## Mapa de discos (confirmar sempre pelo serial/modelo, nunca só pelo número)
| Windows | Modelo | Serial (final) | Porta | Conteúdo |
|---|---|---|---|---|
| Disco 2 | Kingston NV2 500 GB (NVMe) | `…1BA5` | M.2 | Windows 11 (C:) · **EFI do Windows** (300 MB, FAT32) · Recovery (WinRE) |
| Disco 0 | Kingston A400 120 GB | `…D5AA` | SATA 0 | **macOS Sequoia** (APFS) · **EFI com o OpenCore** (200 MB) |
| Disco 1 | Kingston A400 120 GB | `…906D` | SATA 1 (`SATA6G_2`) | "E:" exFAT compartilhado (MSR 16 MB + ~100 MB livres no início) |
| Removível | SanDisk Cruzer 16 GB | — | USB | Pendrive de reserva: OpenCore (`--usb`) + recovery do Sequoia. Liberado para gravação. |

Os números de disco e de partição **mudam** (o diskpart numera pela posição no disco). Conferir com `list partition` / `detail partition` antes de qualquer `select`.

## Estado atual
- OpenCore 1.0.7 no disco do macOS, registrado na BIOS como "OpenCore" (`LauncherOption=Full`), em 1º na ordem de boot. Menu OpenCanopy (GoldenGate), sem timeout, sem verbose.
- SMBIOS MacPro7,1, aplicado só ao macOS (`UpdateSMBIOSMode=Custom`).
- Windows: EFI própria no NV2 (`bcdboot`), WinRE registrado na partição Recovery do NV2. Independente dos SSDs SATA (testado com o SATA 1 desconectado).
- **BitLocker ativo no C:**, TPM com PCRs **0, 2, 4, 11** (Secure Boot desligado, sem PCR7) + senha numérica (backup na conta Microsoft). Lacrado na sequência **BIOS → entrada "OpenCore" → bootmgfw**. Iniciar o Windows por outro caminho (F8, Windows Boot Manager, UEFI OS) → pede a chave.
- `RealTimeIsUniversal=1` no Windows (macOS grava UTC no RTC).
- Inicialização Rápida do Windows **desligada** — manter assim (exFAT compartilhado).
- BIOS 1620 (há a 1806, o usuário optou por não atualizar). Configurações em `docs/historico/fase9-bios.md`; VT-d fica **ligado** (Windows usa VBS/HVCI; macOS usa `DisableIoMapper`).

## Onde está cada coisa
| Caminho | No git? | O quê |
|---|---|---|
| `EFI/` | sim | EFI de referência, SMBIOS placeholder, `LauncherOption=Full` |
| `tools/build_config.py` | sim | **Fonte da verdade do config.plist.** Nunca editar o plist à mão: mudar o script e regenerar |
| `docs/ssdt/*.dsl` | sim | Fontes dos SSDTs gerados pelo SSDTTime |
| `private/smbios.json` | **não** | Serial/MLB/UUID/ROM reais — backup fora do PC é obrigatório |
| `private/EFI/` | **não** | EFI real (= a instalada no disco do macOS) |
| `private/EFI-usb/` | **não** | EFI real do pendrive (`LauncherOption=Disabled`) |
| `private/backup/` | **não** | EFIs anteriores que funcionaram |
| `downloads/`, `tools/ext/`, `acpi/` | não | Releases baixadas, SSDTTime/GenSMBIOS/ProperTree, dump ACPI (tudo recriável) |

## Gerar / validar a config
```bash
X=downloads/x/OpenCore-1.0.7-RELEASE
python -W error tools/build_config.py $X/Docs/Sample.plist EFI/OC/config.plist                                   # git (placeholders)
python -W error tools/build_config.py $X/Docs/Sample.plist private/EFI/OC/config.plist --smbios private/smbios.json      # disco
python -W error tools/build_config.py $X/Docs/Sample.plist private/EFI-usb/OC/config.plist --smbios private/smbios.json --usb  # pendrive
$X/Utilities/ocvalidate/ocvalidate.exe <config.plist>   # mesma versão do OpenCore; exigir "No issues found"
```
Depois de gerar, conferir: o config do git e o de `private/EFI` diferem **só** em `MLB, ROM, SystemSerialNumber, SystemUUID`; o do pendrive difere só em `LauncherOption`. Comentários do plist precisam ser ASCII (o script normaliza).

Se `downloads/` não existir: baixar de novo as releases exatas de `docs/versoes.md` (API do GitHub: `repos/<org>/<repo>/releases/latest`) e extrair em `downloads/x/<nome-do-zip>/`.

## Aplicar uma mudança (fluxo seguro)
1. Mudar `tools/build_config.py` e/ou os arquivos em `EFI/` (copiar para `private/EFI` e `private/EFI-usb` também).
2. Regenerar as 3 configs e validar.
3. **Testar primeiro no pendrive**: backup de `F:\EFI` em `private/backup/`, copiar `private/EFI-usb` → `F:\EFI`, bootar por F8 → "UEFI: SanDisk". (O BitLocker pedirá a chave se o Windows for iniciado por esse caminho — testar só o macOS, ou ter a chave em mãos.)
4. Só então copiar para o disco do macOS:
   - usuário (Admin): `diskpart` → `select disk <A400 …D5AA>` → `list partition` → `select partition <System 200 MB>` → `detail partition` (tipo `c12a7328-f81f-11d2-ba4b-00a0c93ec93b`) → `assign letter=M` → `exit`
   - `robocopy "<repo>\private\EFI" "M:\EFI" /E` (a ESP tem também `EFI\APPLE\UPDATERS` do macOS — **não apagar**; não usar `/MIR`)
   - conferir contagem de arquivos, bytes e hash do `config.plist`; rodar `ocvalidate` em `M:\EFI\OC\config.plist`
   - `diskpart` → mesmo disco/partição → `remove letter=M`
5. Se a mudança alterar a cadeia de boot (OpenCore.efi, BOOTx64.efi, drivers): antes de reiniciar, `manage-bde -protectors -disable C: -RebootCount 1` e iniciar o Windows **pela entrada "OpenCore"** (não F8/UEFI OS). Depois conferir `manage-bde -status C:` = Protection On.
6. Commit (sem segredos). Atualizar `docs/versoes.md` se mudou versão.

## Atualizar OpenCore / kexts
- OpenCore: substituir `BOOTx64.efi`, `OpenCore.efi`, drivers e tools **da mesma release**; regenerar a config a partir do **novo** `Sample.plist` (o script já parte dele) e validar com o **novo** `ocvalidate`. Ler o `Docs/Changelog.md` da versão procurando chaves novas/removidas.
- Kexts: trocar a pasta `.kext` inteira; conferir `CFBundleVersion` no `Info.plist`.
- Sempre pelo fluxo acima (pendrive primeiro). Manter a EFI anterior em `private/backup/`.

## Procedimentos já feitos (referência)
- **EFI do Windows movida para o NV2:** suspender BitLocker → `Resize-Partition` C: −300 MB → `diskpart create partition efi size=300` + `format quick fs=fat32` + `assign letter=S` → `bcdboot C:\Windows /s S: /f UEFI` → reiniciar (BIOS: Windows Boot Manager do NV2) → WinRE: `reagentc /disable`, depois `/enable` falhou (erro 2, tentava usar a ESP) → resolvido dando letra à partição Recovery do NV2 e `reagentc /enable` de novo (ficou em `harddisk2\partition4`, ~627 MB usados). EFI antiga do SATA 1 apagada com `delete partition override`.
- **OpenCore no disco:** ver passo 4 acima. No 1º boot, a sequência F8→UEFI OS é diferente da entrada "OpenCore": o BitLocker pediu a chave uma vez e se relacrou sozinho (evento 793) no caminho definitivo.
- **E: em exFAT:** `Format-Volume -DriveLetter E -FileSystem exFAT` (rótulo ≤ 11 caracteres).

## Problemas conhecidos e diagnóstico
| Sintoma | O que fazer |
|---|---|
| BIOS em safe mode / erro de CMOS ao reiniciar pelo macOS | Já tratado com `DisableRtcChecksum`. Se voltar: RTCMemoryFixup + `rtcfx_exclude` por bisseção (Dortania, "Fixing RTC/CMOS") |
| Windows pede a chave do BitLocker | Ordem de boot mudou (Windows Update/BIOS) ou a cadeia do OpenCore mudou. Digitar a chave; recolocar "OpenCore" em 1º; o Windows relacra sozinho no boot seguinte pelo caminho certo |
| Windows Hello pede novo PIN a cada boot | Log `Microsoft-Windows-HelloForBusiness/Operational` evento 7002 (`0xD000A002`). Visto quando o estado do Secure Boot mudava; recriar o PIN com o boot estável |
| Menu do OpenCore não aparece | BIOS perdeu a entrada: F8 → "UEFI OS (KINGSTON SA400…)" (o OpenCore se registra de novo) ou pendrive |
| macOS não inicia depois de mudança | Pendrive (F8 → SanDisk) ou restaurar `private/backup/`. Diagnóstico: Cmd+V (Win+V) no menu = verbose; para log em arquivo, usar o pacote DEBUG e `Misc/Debug/Target=67` |
| Teclado/mouse mortos no macOS | Primeiro suspeito: `device-id A2AF` do xHCI em DeviceProperties |

Logs úteis no Windows (leitura, sem admin): `Get-WinEvent -LogName 'Microsoft-Windows-BitLocker/BitLocker Management'`, `System` (Kernel-Boot 27/18, TPM-WMI), `C:\Windows\Logs\ReAgent\ReAgent.log`.

## Pendências (opcionais)
- Mapear USB com USBToolBox no Windows (`downloads/x/Windows/`; máx. 15 portas) → `USBToolBox.kext` + `UTBMap.kext`.
- Áudio P2: layout-id 3 não testado (o usuário usa áudio USB). Alternativas 5 → 1 → 11 → 7.
- `ControlMsrE2` para ver o CFG Lock; se destravado, `AppleXcpmCfgLock=False`.
- Conferir que o serial do SMBIOS é inválido em checkcoverage.apple.com (tem CAPTCHA — o usuário faz).
- Testar sleep (MacPro7,1 pode precisar de ajuste).

## Não fazer sem revisão
- **Atualizar para o macOS Tahoe 26**: AppleHDA removido (AppleALC para de funcionar; VoodooHDA com SIP reduzido) e WhateverGreen com problema em AMD no 26. Revisar `docs/historico/fase2-compatibilidade.md` e a página Tahoe da Dortania antes.
- Atualizar a BIOS: suspender o BitLocker antes; depois refazer as configurações da Fase 9 e a entrada "OpenCore".
- Religar o Secure Boot: o OpenCore não é assinado; exigiria vault/chaves próprias.
