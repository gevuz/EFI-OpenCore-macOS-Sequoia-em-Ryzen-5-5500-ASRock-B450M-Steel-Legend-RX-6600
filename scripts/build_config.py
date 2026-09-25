"""
Gera EFI/OC/config.plist a partir do Sample.plist do OpenCore 1.0.7,
seguindo o Dortania (AMD Zen) + AMD_Vanilla, para:
  Ryzen 5 5500 (6 nucleos) / ASRock B450M Steel Legend / RX 6600 / macOS Sequoia.

Uso:  python scripts/build_config.py
- Reproduz o que o ProperTree "OC Snapshot (Clean)" faz para ACPI/Kexts/Drivers/Tools
  (lendo o conteudo real de EFI/OC) e aplica os quirks documentados em README-EFI.md.
- Se existir EFI/OC/Kexts/UTBMap.kext, ele entra no lugar do UTBDefault.kext.
"""
import os, plistlib, copy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OC_DIR = os.path.join(ROOT, "EFI", "OC")
SAMPLE = os.path.join(ROOT, "downloads", "x", "OpenCore-1.0.7-DEBUG", "Docs", "Sample.plist")
AMD_PATCHES = os.path.join(ROOT, "tools", "AMD_Vanilla", "patches.plist")
SMBIOS_TXT = os.path.join(ROOT, "smbios-gerado.txt")

CORE_COUNT = 6          # Ryzen 5 5500: 6 nucleos fisicos (NAO usar threads)
LAYOUT_ID = 11          # ALC897 - alternativas para teste: 31, 12, 13
HDEF_PATH = "PciRoot(0x0)/Pci(0x8,0x1)/Pci(0x0,0x6)"   # AZAL, 1022:15E3 (lido no Windows)
# Ethernet Realtek 10EC:8168 - ACPI GPP3.PT02.PT21 (pontes todas definidas no ACPI, sem SSDT de bridge)
LAN_PATH = "PciRoot(0x0)/Pci(0x2,0x1)/Pci(0x0,0x2)/Pci(0x1,0x0)/Pci(0x0,0x0)"
# Dados pessoais (Serial, MLB, SystemUUID e ROM = MAC real da en0) ficam SOMENTE em smbios-gerado.txt

# Ordem de carregamento: Lilu primeiro, VirtualSMC em seguida, depois plugins Lilu,
# depois kexts independentes, e por fim USBToolBox + mapa (o mapa depende do USBToolBox).
KEXT_ORDER = [
    ("Lilu.kext",                     "Base (patch engine) para os plugins"),
    ("VirtualSMC.kext",               "Emulacao do SMC"),
    ("WhateverGreen.kext",            "Correcoes de GPU (Navi / RX 6600)"),
    ("AppleALC.kext",                 "Audio onboard ALC897"),
    ("RestrictEvents.kext",           "Correcoes para SMBIOS MacPro7,1"),
    ("NVMeFix.kext",                  "Gerenciamento de energia do NVMe de terceiros"),
    ("RealtekRTL8111.kext",           "Ethernet Realtek 10EC:8168"),
    ("AppleMCEReporterDisabler.kext", "Desativa AppleMCEReporter (panics em AMD, macOS 12.3+)"),
    ("USBToolBox.kext",               "USB - base do mapeamento"),
    ("UTBMap.kext",                   "USB - mapa gerado pelo USBToolBox no Windows"),
    ("UTBDefault.kext",               "USB - TEMPORARIO, sem mapa (remover ao ter UTBMap)"),
]


def load_smbios():
    vals = {}
    for line in open(SMBIOS_TXT, encoding="utf-8"):
        line = line.split("#", 1)[0].strip()
        if "=" in line:
            k, v = line.split("=", 1)
            vals[k.strip()] = v.strip()
    return vals


def kext_entry(name, comment):
    kdir = os.path.join(OC_DIR, "Kexts", name)
    info = plistlib.load(open(os.path.join(kdir, "Contents", "Info.plist"), "rb"))
    exe = info.get("CFBundleExecutable", "")
    exe_path = "Contents/MacOS/" + exe if exe and os.path.exists(os.path.join(kdir, "Contents", "MacOS", exe)) else ""
    return {
        "Arch": "Any", "BundlePath": name, "Comment": comment, "Enabled": True,
        "ExecutablePath": exe_path, "MaxKernel": "", "MinKernel": "", "PlistPath": "Contents/Info.plist",
    }


def main():
    cfg = plistlib.load(open(SAMPLE, "rb"))
    smb = load_smbios()

    # ---------------- ACPI ----------------
    amls = sorted(f for f in os.listdir(os.path.join(OC_DIR, "ACPI")) if f.lower().endswith(".aml"))
    comments = {"SSDT-EC.aml": "EC falso (B450 nao tem EC compativel)", "SSDT-USBX.aml": "Propriedades de energia USB"}
    cfg["ACPI"]["Add"] = [{"Comment": comments.get(a, a), "Enabled": True, "Path": a} for a in amls]
    cfg["ACPI"]["Delete"] = []
    cfg["ACPI"]["Patch"] = []   # SSDTTime nao gerou nenhum rename

    # ---------------- Booter ----------------
    cfg["Booter"]["MmioWhitelist"] = []
    cfg["Booter"]["Patch"] = []
    bq = cfg["Booter"]["Quirks"]
    bq.update({
        "AvoidRuntimeDefrag": True,
        "DevirtualiseMmio": False,
        "EnableSafeModeSlide": True,
        "EnableWriteUnprotector": False,
        "ProvideCustomSlide": True,
        "RebuildAppleMemoryMap": True,
        "ResizeAppleGpuBars": -1,
        "SetupVirtualMap": True,
        "SyncRuntimePermissions": True,
    })

    # ---------------- DeviceProperties ----------------
    cfg["DeviceProperties"]["Add"] = {
        HDEF_PATH: {"layout-id": LAYOUT_ID.to_bytes(4, "little")},
        LAN_PATH: {"built-in": bytes([1])},   # en0 como "built-in" (iCloud/App Store)
    }
    cfg["DeviceProperties"]["Delete"] = {}

    # ---------------- Kernel ----------------
    present = set(os.listdir(os.path.join(OC_DIR, "Kexts")))
    order = [k for k in KEXT_ORDER if k[0] in present]
    if "UTBMap.kext" in present:
        order = [k for k in order if k[0] != "UTBDefault.kext"]
    unknown = present - {k[0] for k in KEXT_ORDER}
    if unknown:
        raise SystemExit("Kexts sem ordem definida: %s" % sorted(unknown))
    cfg["Kernel"]["Add"] = [kext_entry(n, c) for n, c in order]
    cfg["Kernel"]["Block"] = []
    cfg["Kernel"]["Force"] = []

    patches = copy.deepcopy(plistlib.load(open(AMD_PATCHES, "rb"))["Kernel"]["Patch"])
    n_core = 0
    for p in patches:
        if "cpuid_cores_per_package" in p["Comment"]:
            r = bytearray(p["Replace"])
            r[1] = CORE_COUNT
            p["Replace"] = bytes(r)
            n_core += 1
    assert n_core == 4, "esperava 4 patches de core count, achei %d" % n_core
    cfg["Kernel"]["Patch"] = patches

    cfg["Kernel"]["Emulate"]["DummyPowerManagement"] = True
    kq = cfg["Kernel"]["Quirks"]
    kq.update({
        "PanicNoKextDump": True,
        "PowerTimeoutKernelPanic": True,
        "ProvideCurrentCpuInfo": True,
        "XhciPortLimit": False,          # nao funciona no macOS 11.3+; USB via USBToolBox
        "DisableLinkeditJettison": True,
    })

    # ---------------- Misc ----------------
    cfg["Misc"]["Boot"]["HideAuxiliary"] = False
    dbg = cfg["Misc"]["Debug"]
    dbg.update({"AppleDebug": True, "ApplePanic": True, "DisableWatchDog": True, "Target": 67})
    sec = cfg["Misc"]["Security"]
    sec.update({
        "AllowSetDefault": True,
        "BlacklistAppleUpdate": True,
        "ScanPolicy": 0,
        "SecureBootModel": "Disabled",
        "Vault": "Optional",
    })
    cfg["Misc"]["Entries"] = []
    shell = next(t for t in cfg["Misc"]["Tools"] if t["Path"] == "OpenShell.efi")
    shell["Enabled"] = True
    cfg["Misc"]["Tools"] = [shell]

    # ---------------- NVRAM ----------------
    boot = cfg["NVRAM"]["Add"]["7C436110-AB2A-4BBB-A880-FE41995C9F82"]
    # Sem npci: o Above 4G Decoding fica LIGADO na BIOS (padrao do Dortania). O README do
    # RealtekRTL8111 manda evitar npci=0x2000/0x3000, e com npci a rede tambem nao subiu.
    boot["boot-args"] = "-v keepsyms=1 debug=0x100 agdpmod=pikera"
    boot["prev-lang:kbd"] = "pt-BR:128"          # Portugues (Brasil) + teclado ABNT2
    boot["csr-active-config"] = bytes.fromhex("00000000")   # SIP ligado
    cfg["NVRAM"]["WriteFlash"] = True

    # ---------------- PlatformInfo ----------------
    gen = cfg["PlatformInfo"]["Generic"]
    gen.update({
        "SystemProductName": smb["Type"],
        "SystemSerialNumber": smb["Serial"],
        "MLB": smb["MLB"],
        "SystemUUID": smb["SystemUUID"],
        "ROM": bytes.fromhex(smb["ROM"]),     # MAC real da en0 (guia iServices do Dortania)
        "SpoofVendor": True,
    })
    cfg["PlatformInfo"]["Automatic"] = True
    cfg["PlatformInfo"]["UpdateSMBIOSMode"] = "Create"

    # ---------------- UEFI ----------------
    template = copy.deepcopy(next(d for d in cfg["UEFI"]["Drivers"] if d["Path"] == "OpenRuntime.efi"))
    drivers = []
    for name, comment in [("OpenRuntime.efi", "Obrigatorio"),
                          ("HfsPlus.efi", "HFS+ (OcBinaryData) - necessario para a recovery"),
                          ("ResetNvramEntry.efi", "Entrada Reset NVRAM no menu")]:
        assert os.path.exists(os.path.join(OC_DIR, "Drivers", name)), name
        d = copy.deepcopy(template)
        d.update({"Path": name, "Comment": comment, "Enabled": True, "LoadEarly": False, "Arguments": ""})
        drivers.append(d)
    cfg["UEFI"]["Drivers"] = drivers
    cfg["UEFI"]["ConnectDrivers"] = True
    cfg["UEFI"]["Quirks"]["UnblockFsConnect"] = False

    out = os.path.join(OC_DIR, "config.plist")
    with open(out, "wb") as f:
        plistlib.dump(cfg, f, sort_keys=True)
    print("config.plist gerado:", out)
    print("Kexts:", ", ".join(n for n, _ in order))


if __name__ == "__main__":
    main()
