# Fase 9 — Configurações da BIOS (ASUS PRIME H410M-E, BIOS 1620)

**Nada disto foi alterado.** Você aplica manualmente (F7 = modo avançado, F10 = salvar). Os nomes/caminhos são os típicos da UEFI ASUS série 400 e **precisam ser confirmados pelas fotos** da sua BIOS; se uma opção não existir, anote e siga.

## Antes de mexer (Windows)
1. **BitLocker está ATIVO no C:** (confirmado: desligar o Secure Boot abriu a tela de recuperação). Procedimento, no PowerShell **como Administrador**:
   1. Salvar a chave de recuperação fora do PC: `manage-bde -protectors -get C:` (anote a "Senha Numérica" de 48 dígitos; ela também fica em account.microsoft.com/devices/recoverykey).
   2. Suspender por 2 reinícios: `manage-bde -protectors -disable C: -RebootCount 2`
   3. Reiniciar → BIOS → Secure Boot `OS Type = Other OS` → F10. O Windows sobe sem pedir chave e o BitLocker volta sozinho, lacrado no novo estado.
   - **Dual boot:** inicie o Windows pelo Windows Boot Manager (1º na ordem de boot / F8), **não** pelo picker do OpenCore — passar pelo OpenCore muda as medições do TPM e pode pedir a chave de novo.
2. Salve o perfil atual da BIOS: Tool → ASUS User Profile → salvar (volta atrás fácil).

## Desligar
| Nome | Caminho típico | Valor | Motivo |
|---|---|---|---|
| Fast Boot | Boot → Fast Boot | Disabled | Garante que o USB seja inicializado e o picker do OpenCore apareça |
| Secure Boot | Boot → Secure Boot → OS Type | **Other OS** | O OpenCore não é assinado com as chaves da Microsoft |
| CSM | Boot → CSM → Launch CSM | Disabled | Só UEFI; exigido pela GOP da RX 6600 |
| Serial Port | Advanced → Onboard Devices → Serial Port Configuration | Off | Porta serial causa panics no macOS (Dortania) |
| Intel SGX | Advanced → CPU Configuration → SGX | Disabled | Dortania: desligar |
| Intel PTT (fTPM) | Advanced → PCH-FW Configuration → PTT | **Manter** | Windows 11 depende dele; o macOS não é afetado |
| VT-d | Advanced → System Agent Configuration → VT-d | Pode ficar ligado | Coberto por `DisableIoMapper=YES` |
| CFG Lock | Normalmente não exibido na ASUS | — | Coberto por `AppleXcpmCfgLock=YES` |

## Ligar
| Nome | Caminho típico | Valor | Motivo |
|---|---|---|---|
| Above 4G Decoding | Advanced → PCI Subsystem Settings | Enabled | Dortania: obrigatório para GPUs modernas |
| Re-Size BAR Support | Advanced → PCI Subsystem Settings | Disabled **ou** Enabled + mudar `ResizeAppleGpuBars` para 0 | macOS não lida com BAR grande; a config atual (-1) assume **Disabled** |
| Intel Virtualization (VT-x) | Advanced → CPU Configuration | Enabled | Dortania |
| Hyper-Threading | Advanced → CPU Configuration | Enabled | 6C/12T |
| Execute Disable Bit | Advanced → CPU Configuration | Enabled | Dortania |
| XHCI/EHCI Hand-off | Advanced → USB Configuration | Enabled (se existir) | Dortania |
| SATA Mode | Advanced → PCH Storage Configuration | AHCI (já está) | Inventário confirmou AHCI |
| Primary Display | Advanced → System Agent → Graphics Configuration | PEG | Não há iGPU (10400F) |

## Ordem de boot
Deixe o **Windows Boot Manager** como primeiro. Para o macOS, use o menu de boot (F8) até o OpenCore estar no disco (Fase 13).

## Confirmado pelas fotos (BIOS 1620)
- Boot → CSM → Launch CSM = Disabled ✅
- Boot → Boot Configuration → Fast Boot = Disabled ✅
- Boot → Secure Boot → OS Type: `Other OS` só depois de suspender o BitLocker (acima)
- Advanced → CPU Configuration: SGX Disabled ✅, Intel (VMX) Virtualization Enabled ✅, Hyper-Threading Enabled ✅
- CFG Lock não aparece em CPU Configuration → mantém `AppleXcpmCfgLock=YES`
- Advanced → PCI Subsystem Settings: Above 4G Decoding Enabled ✅, Re-Size BAR Disabled ✅ (casa com `ResizeAppleGpuBars=-1`), SR-IOV Disabled ✅
- Advanced → USB Configuration: XHCI Hand-off Enabled ✅, Legacy USB Support Enabled ✅
- Advanced → System Agent: VT-d Enabled + "Control Iommu Pre-boot Behavior = Disable IOMMU" → **manter**. O Windows usa VT-d (VBS/Memory Integrity ativos) e o macOS ignora via `DisableIoMapper=YES`.
- Advanced → Onboard Devices: HD Audio Enabled ✅, Realtek LAN Enabled ✅; Serial Port Configuration → submenu a conferir (deve ficar Off)

## Fotos que ainda preciso
Boot (Fast Boot, CSM, Secure Boot), Advanced → CPU Configuration, PCI Subsystem Settings, USB Configuration, Onboard Devices Configuration, System Agent Configuration.
