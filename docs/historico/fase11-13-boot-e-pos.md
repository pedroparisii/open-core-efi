# Fases 11–13 — Primeiro boot, debug e pós-instalação

## Fase 11 — Checklist antes do primeiro boot
- [ ] BitLocker verificado / chave salva (ver `fase9-bios.md`).
- [ ] BIOS configurada conforme `fase9-bios.md` e salva (F10).
- [ ] Pendrive (F:) contém `EFI/` e `com.apple.recovery.boot/` na raiz.
- [ ] Monitor no **DisplayPort** da RX 6600.
- [ ] Teclado e mouse em portas USB **traseiras** (evite hubs); o dongle AIC8800 pode ser removido.
- [ ] Cabo de rede ligado (o recovery baixa o macOS inteiro pela internet via RTL8111).
- [ ] D: (Disco 0) é o único disco a ser apagado.

**Menu de boot ASUS:** ligue e aperte **F8** repetidamente → escolha a entrada **UEFI: SanDisk…** (partição 1). No picker do OpenCore escolha a entrada do recovery (`macOS Base System` / `Install macOS Sequoia`). Primeiro, rode `ControlMsrE2` (barra de espaço mostra as ferramentas) e anote se o CFG Lock está travado.

**Identificar o disco no Utilitário de Disco** ("Mostrar todos os dispositivos"): dois `KINGSTON SA400S37120G` de 120 GB. O certo (Disco 0) tem **uma** partição de dados (~111,8 GB) e **nenhuma EFI de 100 MB**. O errado (Disco 1) tem a EFI de 100 MB — é o boot do Windows. Apague o disco inteiro (nível de dispositivo) como **APFS / Mapa de Partição GUID**, nome `macOS`. Na dúvida, pare e me mande foto.

## Fase 12 — Debug (uma mudança por vez)
| Sintoma | Primeiro teste | Segundo teste |
|---|---|---|
| Teclado/mouse mortos no picker ou instalador | Portas traseiras USB 2.0 | Remover a entrada `device-id` do xHCI em DeviceProperties |
| Para em `[EB|#LOG:EXITBS:START]` | Conferir BIOS (CSM off, Above 4G on) | `DevirtualiseMmio` → NO |
| Tela preta após o verbose | Outra porta DP da placa | Remover `agdpmod=pikera` |
| Panic de AppleACPIPlatform / trava cedo | Foto do panic | Desativar um SSDT de cada vez |
| Não vê discos | Utilitário de Disco → "Mostrar todos os dispositivos" | — |
| Instalação reinicia no meio | Normal: escolha `macOS Installer` no picker até sumir | — |

Se nada disso bastar: trocar para o pacote **DEBUG** da 1.0.7 (`OpenCore.efi`, `BOOTx64.efi`, `OpenRuntime.efi`) e `Misc → Debug → Target = 67`, que grava `opencore-*.txt` na raiz do pendrive.

## Fase 13 — Pós-instalação
1. **Rede**: conferir `en0` (RTL8111). Se o link cair/voltar, desligar EEE no Ajustes de Rede.
2. **GPU**: Metal/aceleração em Informações do Sistema; testar vídeo HEVC.
3. **CPU**: `sysctl machdep.xcpm.mode` = 1; se o CFG Lock estiver destravado, desligar `AppleXcpmCfgLock`.
4. **Áudio**: testar layout-id 3; se não houver som/entradas, testar 5 → 1 → 11 → 7 (um reboot por valor).
5. **USB**: mapear no Windows com USBToolBox (`downloads/x/Windows/`), no máximo 15 portas, gerar `UTBMap.kext` + `USBToolBox.kext`.
6. **NVRAM**: nativa na série 400 — testar com `sudo nvram test=1`, reiniciar, `nvram test`.
7. **Sleep**: `pmset -g`; MacPro7,1 pode exigir ajuste (Dortania "Fixing Sleep").
8. **OpenCore no disco**: copiar a EFI para a ESP **do disco do macOS (Disco 0)** — nunca para a ESP do Disco 1 (Windows). Depois: `ScanPolicy`, `Target` e `-v` reduzidos, `Timeout`.
9. **Backup da EFI**: manter o pendrive funcionando como reserva.
10. **Relógio no dual boot**: no Windows (admin) `reg add "HKLM\SYSTEM\CurrentControlSet\Control\TimeZoneInformation" /v RealTimeIsUniversal /t REG_DWORD /d 1 /f` — mostrado aqui, **não executado**.
11. **Serial**: confirmar em checkcoverage.apple.com que o serial gerado é **inválido** (você faz; tem CAPTCHA) antes de logar no iCloud/iMessage.
