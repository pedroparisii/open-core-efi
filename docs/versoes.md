# Versões usadas (baixadas em 2026-09-27)

Todas dos repositórios oficiais, release mais recente na data. SSDTTime, GenSMBIOS e ProperTree não publicam releases: foi usado o HEAD do `master` (commit anotado).

| Componente | Versão | Fonte |
|---|---|---|
| OpenCore (RELEASE + DEBUG) | **1.0.7** (2026-03-20) | acidanthera/OpenCorePkg |
| ocvalidate / macserial / macrecovery | 1.0.7 (do mesmo zip) | acidanthera/OpenCorePkg |
| Lilu | 1.7.2 | acidanthera/Lilu |
| VirtualSMC (+SMCProcessor, SMCSuperIO) | 1.3.7 | acidanthera/VirtualSMC |
| WhateverGreen | 1.7.0 | acidanthera/WhateverGreen |
| AppleALC | 1.9.7 | acidanthera/AppleALC |
| RestrictEvents | 1.1.6 | acidanthera/RestrictEvents |
| NVMeFix | 1.1.3 | acidanthera/NVMeFix |
| RealtekRTL8111 | 3.0.0 (bundle 3.0.4) | Mieze/RTL8111_driver_for_OS_X |
| USBToolBox (tool Windows / kext) | 0.2 / 1.2.0 | USBToolBox/tool, USBToolBox/kext |
| SSDTTime | `de49a3a` (2026-08-23) | corpnewt/SSDTTime |
| GenSMBIOS | `9a44698` (2026-01-04) | corpnewt/GenSMBIOS |
| ProperTree | `51ed53d` (2026-06-20) | corpnewt/ProperTree |
| iasl / acpidump | 20251212 (baixados pelo SSDTTime) | Open-ACPICA |
| macOS | **Sequoia 15** (recovery via board-id `Mac-7BA5B2D9E42DDD94`) | Apple (macrecovery.py) |

Reproduzir a config: `python tools/build_config.py downloads/x/OpenCore-1.0.7-RELEASE/Docs/Sample.plist EFI/OC/config.plist`.
