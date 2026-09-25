"""
Leitor de portas USB (somente leitura) para os controladores XHCI desta placa.

Existe porque o usbdump do USBToolBox 0.2 embaralha os controladores quando o
"Parsec Virtual USB Adapter" esta presente e perde o XHC0.
Usa as mesmas IOCTLs de leitura do USBView da Microsoft, direto em cada root hub.

Uso:
  python scripts/usb_ports.py            -> fotografia atual
  python scripts/usb_ports.py --watch    -> fica monitorando e acumula em usb-descoberta.json
"""
import ctypes, ctypes.wintypes as wt, json, os, sys, time, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "usb-descoberta.json")
HUB_GUID = "{f18a0e88-c30c-11d0-8815-00a0c906bed8}"

def detect_controllers():
    """Controladores XHCI PCI reais (ignora adaptadores virtuais como o do Parsec) -> {instance_id: nome ACPI}."""
    ps = (
        "Get-PnpDevice -PresentOnly | Where-Object { $_.InstanceId -like 'PCI\\*' } | ForEach-Object { "
        "$s=(Get-PnpDeviceProperty -InstanceId $_.InstanceId -KeyName DEVPKEY_Device_Service).Data; "
        "if ($s -eq 'USBXHCI') { $a=(Get-PnpDeviceProperty -InstanceId $_.InstanceId -KeyName DEVPKEY_Device_BiosDeviceName).Data; "
        "\"$($_.InstanceId)|$a\" } }"
    )
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True).stdout
    ctrls = {}
    for line in out.splitlines():
        if "|" not in line:
            continue
        inst, acpi = line.strip().split("|", 1)
        name = acpi.rsplit(".", 1)[-1] if acpi else inst.rsplit("&", 1)[-1]
        ctrls[inst] = name
    return ctrls

def ctl(func):
    return (0x22 << 16) | (func << 2)

# Todas de LEITURA (usbioctl.h). Nunca usar 273 (HUB_CYCLE_PORT) nem 275 (RESET_HUB).
IOCTL_NODE_INFO = ctl(258)             # USB_GET_NODE_INFORMATION
IOCTL_CONN_INFO_EX = ctl(274)          # USB_GET_NODE_CONNECTION_INFORMATION_EX
IOCTL_PORT_CONNECTOR_PROPS = ctl(278)  # USB_GET_PORT_CONNECTOR_PROPERTIES
IOCTL_CONN_INFO_EX_V2 = ctl(279)       # USB_GET_NODE_CONNECTION_INFORMATION_EX_V2

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.CreateFileW.restype = wt.HANDLE
k32.CreateFileW.argtypes = [wt.LPCWSTR, wt.DWORD, wt.DWORD, wt.LPVOID, wt.DWORD, wt.DWORD, wt.HANDLE]
k32.DeviceIoControl.argtypes = [wt.HANDLE, wt.DWORD, wt.LPVOID, wt.DWORD, wt.LPVOID, wt.DWORD, ctypes.POINTER(wt.DWORD), wt.LPVOID]
INVALID = wt.HANDLE(-1).value


def ioctl(h, code, inbuf, outsize):
    buf = ctypes.create_string_buffer(bytes(inbuf).ljust(outsize, b"\0"), outsize)
    ret = wt.DWORD(0)
    ok = k32.DeviceIoControl(h, code, buf, len(inbuf), buf, outsize, ctypes.byref(ret), None)
    return buf.raw[: ret.value] if ok else None


def root_hub_instance(ctrl_id):
    ps = f"(Get-PnpDeviceProperty -InstanceId '{ctrl_id}' -KeyName DEVPKEY_Device_Children).Data"
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True).stdout.split()
    return next((x for x in out if x.upper().startswith("USB\\ROOT_HUB")), None)


def read_hub(path):
    h = k32.CreateFileW(path, 0x40000000, 0x2, None, 3, 0, None)  # GENERIC_WRITE, FILE_SHARE_WRITE, OPEN_EXISTING
    if h == INVALID or h is None:
        raise OSError(f"nao abriu {path}: erro {ctypes.get_last_error()}")
    try:
        ni = ioctl(h, IOCTL_NODE_INFO, b"", 256)
        nports = ni[6]
        ports = []
        for i in range(1, nports + 1):
            idx = i.to_bytes(4, "little")
            # USB_PORT_CONNECTOR_PROPERTIES tem 20 bytes (com padding)
            pcp = ioctl(h, IOCTL_PORT_CONNECTOR_PROPS, idx + b"\0" * 16, 512)
            if pcp is None:
                print(f"  aviso: PORT_CONNECTOR_PROPERTIES falhou na porta {i}: erro {ctypes.get_last_error()}", file=sys.stderr)
                pcp = b"\0" * 20
            props = int.from_bytes(pcp[8:12], "little")
            companion = int.from_bytes(pcp[14:16], "little")
            v2 = ioctl(h, IOCTL_CONN_INFO_EX_V2, idx + (16).to_bytes(4, "little") + (0b111).to_bytes(4, "little") + b"\0" * 4, 16) or b"\0" * 16
            protos = int.from_bytes(v2[8:12], "little")
            flags = int.from_bytes(v2[12:16], "little")
            ce = ioctl(h, IOCTL_CONN_INFO_EX, idx, 512)
            dev = None
            if ce and len(ce) >= 35 and int.from_bytes(ce[31:35], "little") == 1:  # DeviceConnected
                vid = int.from_bytes(ce[12:14], "little"); pid = int.from_bytes(ce[14:16], "little")
                speed = ce[23]
                if flags & 0b100: sp = "USB3.1+"
                elif flags & 0b1: sp = "USB3"
                else: sp = {0: "USB1-Low", 1: "USB1-Full", 2: "USB2"}.get(speed, str(speed))
                dev = {"id": f"{vid:04x}:{pid:04x}", "speed": sp, "hub": bool(ce[24])}
            ports.append({
                "index": i,
                "protocol": "USB3" if protos & 0b100 else ("USB2" if protos & 0b10 else "USB1"),
                "companion": companion or None,
                "user_connectable": bool(props & 1),
                "type_c": bool(props & 0b1000),
                "device": dev,
            })
        return ports
    finally:
        k32.CloseHandle(h)


def snapshot(hub_paths):
    return {name: read_hub(path) for name, path in hub_paths.items()}


def main():
    hub_paths = {}
    for cid, name in detect_controllers().items():
        rh = root_hub_instance(cid)
        hub_paths[name] = "\\\\?\\" + rh.replace("\\", "#") + "#" + HUB_GUID
    if "--watch" not in sys.argv:
        print(json.dumps(snapshot(hub_paths), indent=1))
        return
    acc = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    while True:
        snap = snapshot(hub_paths)
        for name, ports in snap.items():
            cacc = acc.setdefault(name, {})
            for p in ports:
                e = cacc.setdefault(str(p["index"]), {k: p[k] for k in ("index", "protocol", "companion", "user_connectable", "type_c")} | {"seen": []})
                if p["device"]:
                    tag = f"{p['device']['id']} {p['device']['speed']}"
                    if tag not in e["seen"]:
                        e["seen"].append(tag)
                        print(time.strftime("%H:%M:%S"), f"{name} porta {p['index']} ({p['protocol']}): {tag}", flush=True)
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(acc, f, indent=1)
        time.sleep(1)


if __name__ == "__main__":
    main()
