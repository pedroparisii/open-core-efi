"""Gera o config.plist do OpenCore 1.0.7 a partir do Sample.plist oficial.

Hardware-alvo: i5-10400F (Comet Lake, sem iGPU) / ASUS PRIME H410M-E / RX 6600 /
ALC887 / RTL8111H. macOS alvo: Sequoia 15. Cada escolha está justificada nos
comentários (Dortania Comet Lake + Configuration.pdf da 1.0.7).

Uso:
  python tools/build_config.py SAMPLE OUT                 -> SMBIOS com placeholders (vai para o git)
  python tools/build_config.py SAMPLE OUT --smbios J.json -> SMBIOS real (NUNCA commitar)
  ... --smbios J.json --usb                               -> pendrive de reserva (LauncherOption=Disabled)
"""
import argparse
import json
import plistlib
import unicodedata


SSDTS = [
    ("SSDT-PLUG.aml", "CPU: plugin-type=1 em \\_SB.PR00 (XCPM)"),
    ("SSDT-EC.aml", "EC falso: H_EC do DSDT tem _STA=0"),
    ("SSDT-USBX.aml", "Energia USB para SMBIOS Skylake+"),
    ("SSDT-RTCAWAC.aml", "STAS=1 no Darwin: liga RTC legado, desliga AWAC"),
    ("SSDT-USB-Reset.aml", "Desliga XHC.RHUB no Darwin (placas ASUS série 400)"),
]

# Ordem importa: Lilu antes dos plugins; VirtualSMC antes dos plugins SMC.
KEXTS = [
    ("Lilu.kext", "Lilu", "Patch engine"),
    ("VirtualSMC.kext", "VirtualSMC", "Emulação do SMC"),
    ("SMCProcessor.kext", "SMCProcessor", "Sensores da CPU Intel"),
    ("SMCSuperIO.kext", "SMCSuperIO", "Sensores de ventoinha (Super I/O)"),
    ("WhateverGreen.kext", "WhateverGreen", "Correções de GPU AMD"),
    ("AppleALC.kext", "AppleALC", "Áudio ALC887 (layout-id em DeviceProperties)"),
    ("RestrictEvents.kext", "RestrictEvents", "MacPro7,1: avisos de PCI/RAM + OTA (sbvmm)"),
    ("NVMeFix.kext", "NVMeFix", "Energia do NVMe não-Apple (Kingston NV2)"),
    ("RealtekRTL8111.kext", "RealtekRTL8111", "Ethernet RTL8111H 10EC:8168"),
]

DRIVERS = [
    ("OpenRuntime.efi", "Obrigatório (quirks de Booter/memória)"),
    ("OpenHfsPlus.efi", "Ler a partição HFS+ do instalador/recovery"),
    ("ResetNvramEntry.efi", "Entrada 'Reset NVRAM' no picker"),
    ("OpenCanopy.efi", "Picker grafico (Resources do OcBinaryData)"),
]

TOOLS = [
    ("OpenShell.efi", "OpenShell", "Shell UEFI"),
    ("ControlMsrE2.efi", "ControlMsrE2", "Ler estado do CFG Lock (MSR 0xE2)"),
]

PCI_HDA = "PciRoot(0x0)/Pci(0x1F,0x3)"
PCI_XHC = "PciRoot(0x0)/Pci(0x14,0x0)"
NVRAM_APPLE = "7C436110-AB2A-4BBB-A880-FE41995C9F82"

PLACEHOLDER_SMBIOS = {
    "SystemSerialNumber": "W00000000001",
    "MLB": "M0000000000000001",
    "SystemUUID": "00000000-0000-0000-0000-000000000000",
    "ROM": "112233445566",
}


def ascii_only(text):
    """OpenCore rejeita caracteres fora de ASCII em Comment (ocvalidate)."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()


def build(sample_path, smbios):
    with open(sample_path, "rb") as f:
        c = plistlib.load(f)

    # ---------------- ACPI ----------------
    # Só SSDTs gerados pelo SSDTTime a partir do DSDT desta placa; nenhum rename
    # necessário (patches_OC.plist do SSDTTime veio sem ACPI->Patch).
    c["ACPI"]["Add"] = [{"Comment": ascii_only(cm), "Enabled": True, "Path": p} for p, cm in SSDTS]
    c["ACPI"]["Delete"] = []
    c["ACPI"]["Patch"] = []
    for k in c["ACPI"]["Quirks"]:
        c["ACPI"]["Quirks"][k] = False

    # ---------------- Booter (Dortania Comet Lake) ----------------
    c["Booter"]["MmioWhitelist"] = []
    c["Booter"]["Patch"] = []
    bq = c["Booter"]["Quirks"]
    bq.update({
        "AvoidRuntimeDefrag": True,
        "DevirtualiseMmio": True,
        "EnableSafeModeSlide": True,
        "EnableWriteUnprotector": False,  # substituído por RebuildAppleMemoryMap+SyncRuntimePermissions
        "ProtectUefiServices": True,
        "ProvideCustomSlide": True,
        "RebuildAppleMemoryMap": True,
        "ResizeAppleGpuBars": -1,  # mudar para 0 se Re-Size BAR estiver ligado na BIOS
        "SetupVirtualMap": False,  # quebrado nas proteções de memória do Comet Lake
        "SyncRuntimePermissions": True,
    })

    # ---------------- DeviceProperties ----------------
    c["DeviceProperties"]["Add"] = {
        # ALC887 (subsystem 1043:86C7), 3 conectores traseiros + painel frontal.
        # Nenhum layout do AppleALC é específico da H410M-E; 3 = "3 audio ports,
        # native: 2 inputs, 1 output + front panel". Alternativas: 5, 1, 11, 7.
        PCI_HDA: {"layout-id": (3).to_bytes(4, "little")},
        # xHCI 8086:A3AF (PCH-V). Os IDs do PCH-V espelham o PCH série 200
        # (A382/A282, A3F0/A2F0, A3A3/A2A3), então apresentamos o A2AF nativo.
        PCI_XHC: {"device-id": bytes.fromhex("AFA20000")},
    }
    c["DeviceProperties"]["Delete"] = {}

    # ---------------- Kernel ----------------
    add = []
    for bundle, exe, comment in KEXTS:
        add.append({
            "Arch": "x86_64", "BundlePath": bundle, "Comment": ascii_only(comment), "Enabled": True,
            "ExecutablePath": "Contents/MacOS/" + exe, "MaxKernel": "", "MinKernel": "",
            "PlistPath": "Contents/Info.plist",
        })
    c["Kernel"]["Add"] = add
    c["Kernel"]["Block"] = []
    c["Kernel"]["Force"] = []
    c["Kernel"]["Patch"] = []
    kq = c["Kernel"]["Quirks"]
    kq.update({
        "AppleXcpmCfgLock": True,   # BIOS ASUS não expõe CFG Lock; rever com ControlMsrE2
        "CustomSMBIOSGuid": True,   # par com UpdateSMBIOSMode=Custom
        "DisableIoMapper": True,    # DMAR tem Reserved Memory Region; README do RTL8111 recomenda AppleVTD off na dúvida
        "DisableLinkeditJettison": True,
        # BIOS entrava em safe mode ao reiniciar pelo macOS (Dortania: RTC/CMOS).
        # 1o passo oficial; se não resolver, RTCMemoryFixup com rtcfx_exclude.
        "DisableRtcChecksum": True,
        "PanicNoKextDump": True,
        "PowerTimeoutKernelPanic": True,
        "XhciPortLimit": False,     # sem efeito a partir do macOS 11.3
    })

    # ---------------- Misc ----------------
    boot = c["Misc"]["Boot"]
    boot.update({
        "HideAuxiliary": True,
        "LauncherOption": "Full",        # entrada "OpenCore" na BIOS; Windows Update não a tira do topo
        "PickerMode": "External",        # OpenCanopy
        "PickerVariant": "Acidanthera\\GoldenGate",
        "PollAppleHotKeys": True,        # Cmd+V (verbose) / Shift (safe mode) direto no picker
        "ShowPicker": True,
        "Timeout": 0,                    # espera a escolha do usuário
    })
    dbg = c["Misc"]["Debug"]
    # Uso diário (Dortania, pós-instalação): sem logs em arquivo nem watchdog desligado.
    dbg.update({"AppleDebug": False, "ApplePanic": False, "DisableWatchDog": False, "Target": 3})
    sec = c["Misc"]["Security"]
    sec.update({
        "AllowSetDefault": True,     # Ctrl+Enter no picker define o padrão
        "BlacklistAppleUpdate": True,
        "ScanPolicy": 0,             # todos os discos, inclusive USB (pendrive de reserva)
        # Sequoia (14.4+): OTA só funciona com SecureBootModel=Disabled + revpatch=sbvmm
        "SecureBootModel": "Disabled",
        "Vault": "Optional",         # sem vault assinado
    })
    c["Misc"]["Entries"] = []
    c["Misc"]["Tools"] = [{
        "Arguments": "", "Auxiliary": True, "Comment": ascii_only(cm), "Enabled": True, "Flavour": "Auto",
        "FullNvramAccess": False, "Name": name, "Path": path, "RealPath": False, "TextMode": False,
    } for path, name, cm in TOOLS]

    # ---------------- NVRAM ----------------
    nv = c["NVRAM"]["Add"][NVRAM_APPLE]
    nv["boot-args"] = "keepsyms=1 agdpmod=pikera revpatch=sbvmm,pci"  # sem -v/debug: boot limpo
    nv["csr-active-config"] = bytes(4)
    nv.pop("prev-lang:kbd", None)       # idioma é escolhido no instalador
    nv.pop("#INFO (prev-lang:kbd)", None)

    # ---------------- PlatformInfo ----------------
    # MacPro7,1: único SMBIOS sem expectativa de iGPU que é suportado no Sequoia E no Tahoe.
    g = c["PlatformInfo"]["Generic"]
    g["SystemProductName"] = "MacPro7,1"
    g["SystemSerialNumber"] = smbios["SystemSerialNumber"]
    g["MLB"] = smbios["MLB"]
    g["SystemUUID"] = smbios["SystemUUID"]
    g["ROM"] = bytes.fromhex(smbios["ROM"].replace(":", "").replace("-", ""))
    c["PlatformInfo"]["UpdateSMBIOSMode"] = "Custom"  # SMBIOS exclusivo do macOS (Windows intacto)

    # ---------------- UEFI ----------------
    c["UEFI"]["Drivers"] = [{
        "Arguments": "", "Comment": ascii_only(cm), "Enabled": True, "LoadEarly": False, "Path": p,
    } for p, cm in DRIVERS]
    c["UEFI"]["Quirks"].update({"RequestBootVarRouting": True, "ResizeGpuBars": -1, "UnblockFsConnect": False})

    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sample")
    ap.add_argument("out")
    ap.add_argument("--smbios", help="JSON com SystemSerialNumber, MLB, SystemUUID, ROM")
    ap.add_argument("--usb", action="store_true",
                    help="pendrive de reserva: não registrar o OpenCore do USB na BIOS")
    a = ap.parse_args()
    smbios = PLACEHOLDER_SMBIOS
    if a.smbios:
        with open(a.smbios, encoding="utf-8") as f:
            smbios = json.load(f)
    cfg = build(a.sample, smbios)
    if a.usb:
        cfg["Misc"]["Boot"]["LauncherOption"] = "Disabled"
    with open(a.out, "wb") as f:
        plistlib.dump(cfg, f, sort_keys=True)
    print("gerado:", a.out)


if __name__ == "__main__":
    main()
