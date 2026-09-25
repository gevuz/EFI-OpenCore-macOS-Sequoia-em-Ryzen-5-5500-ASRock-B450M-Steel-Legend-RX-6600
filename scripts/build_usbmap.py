"""
Gera EFI/OC/Kexts/UTBMap.kext no mesmo formato do USBToolBox 0.2 (base.py -> build_kext),
a partir de usb-descoberta.json (scripts/usb_ports.py --watch).

Criterio: entram todas as portas que o firmware declara como conectaveis pelo usuario
(nenhum controlador passa de 15 portas, entao nao ha necessidade de cortar).
As portas internas nao-conectaveis (XHC0/XHC1 3 e 4) ficam de fora.

Tipos (UsbConnector): 0 = USB2 Type-A, 3 = USB3 Type-A, 10 = Type-C com switch, 255 = interna.
"""
import json, os, plistlib, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISC = os.path.join(ROOT, "usb-descoberta.json")
TEMPLATE = os.path.join(ROOT, "tools", "USBToolBox-tool", "resources", "Info.plist")
OUT = os.path.join(ROOT, "EFI", "OC", "Kexts", "UTBMap.kext")

# Ajustes manuais de tipo: {("PTXH", indice_da_porta_USB3): 10} quando a USB-C for identificada
TYPE_OVERRIDES = {}

CTRL_DESC = {
    "XHC0": "CPU (Cezanne) - 2 das USB 3.2 Gen1 traseiras",
    "XHC1": "CPU (Cezanne) - 2 das USB 3.2 Gen1 traseiras",
    "PTXH": "Chipset B450 - Gen2 A/C traseiras, USB3 frontal, USB 2.0",
}
NAMES = {  # nomes amigaveis dos dispositivos vistos, so para os comentarios
    "046d:0825": "webcam C270", "0d8c:0012": "C-Media audio", "25a7:fa7c": "receptor 2.4G",
    "25a7:fa7b": "receptor 2.4G", "3142:a010": "mic fifine", "258a:0049": "teclado",
    "2b89:6275": "BT Realtek", "058f:6387": "pendrive USB2",
}


def le32(n):
    return n.to_bytes(4, "little")


def main():
    disc = json.load(open(DISC, encoding="utf-8"))
    info = plistlib.load(open(TEMPLATE, "rb"))
    info["OSBundleLibraries"] = {"com.dhinakg.USBToolBox.kext": "1.0.0"}
    for ctrl, ports in disc.items():
        ports = sorted(ports.values(), key=lambda p: p["index"])
        by_index = {p["index"]: p for p in ports}
        selected = [p for p in ports if p["user_connectable"]]
        pers = {
            "CFBundleIdentifier": "com.dhinakg.USBToolBox.kext",
            "IOClass": "USBToolBox",
            "IOProviderClass": "IOPCIDevice",
            "IOMatchCategory": "USBToolBox",
            "IONameMatch": ctrl,
            "IOProviderMergeProperties": {"ports": {}, "port-count": le32(max(p["index"] for p in selected))},
        }
        counters = {"HS": 1, "SS": 1}
        for p in selected:
            prefix = "SS" if p["protocol"] == "USB3" else "HS"
            name = f"{prefix}{counters[prefix]:02d}"
            counters[prefix] += 1
            usb3_pair = p["protocol"] == "USB3" or (p["companion"] and by_index[p["companion"]]["protocol"] == "USB3")
            ss_index = p["index"] if p["protocol"] == "USB3" else p["companion"]
            ctype = TYPE_OVERRIDES.get((ctrl, ss_index), 3 if usb3_pair else 0)
            seen = sorted({NAMES.get(s.split()[0], s.split()[0]) for s in p["seen"]})
            comp = by_index.get(p["companion"]) if p["companion"] else None
            seen_pair = sorted({NAMES.get(s.split()[0], s.split()[0]) for s in comp["seen"]}) if comp else []
            comment = f"{ctrl} porta {p['index']} ({p['protocol']}" + (f", par da {p['companion']}" if p["companion"] else "") + ")"
            if seen:
                comment += " - visto: " + ", ".join(seen)
            elif seen_pair:
                comment += " - porta fisica confirmada pelo par (visto la: " + ", ".join(seen_pair) + ")"
            else:
                comment += " - nao testada (declarada conectavel pelo firmware)"
            pers["IOProviderMergeProperties"]["ports"][name] = {
                "port": le32(p["index"]), "UsbConnector": ctype, "#comment": comment,
            }
        info["IOKitPersonalities"][ctrl] = pers
        print(f"{ctrl}: {len(selected)} portas ({CTRL_DESC.get(ctrl, '')})")
        for n, v in pers["IOProviderMergeProperties"]["ports"].items():
            print(f"   {n}  port={int.from_bytes(v['port'], 'little'):>2}  tipo={v['UsbConnector']:>3}  {v['#comment']}")
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "Contents"))
    with open(os.path.join(OUT, "Contents", "Info.plist"), "wb") as f:
        plistlib.dump(info, f, sort_keys=True)
    print("UTBMap.kext gerado em", OUT)


if __name__ == "__main__":
    main()
