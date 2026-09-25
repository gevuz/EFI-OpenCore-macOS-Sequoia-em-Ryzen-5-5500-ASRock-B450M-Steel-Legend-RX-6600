# EFI OpenCore: macOS Sequoia em Ryzen 5 5500 + ASRock B450M Steel Legend + RX 6600

> **Status:** ✅ instalado e funcionando (macOS 15.8), testes em andamento. Veja a [tabela de testes](#4-status-dos-testes).
> OpenCore **1.0.7** · macOS **15 Sequoia** · AMD **Zen 3 (Cezanne)** · chipset **B450** · GPU **Navi 23**

**English TL;DR:** OpenCore 1.0.7 EFI for macOS Sequoia on a Ryzen 5 5500 / ASRock B450M Steel Legend / RX 6600. It was built only from the Dortania guide, AMD_Vanilla and official GitHub releases. This README is in Portuguese and is structured so you can hand it to an AI coding agent (Claude Code, Codex, Cursor…) to adapt the EFI to your own hardware (see [section 8](#8-prompt-pronto-para-colar-no-seu-agente)). **The SMBIOS is blank on purpose: generate your own.**

Eu buscava ajuda e pouca gente passava a informação completa. Então aqui está tudo: o que foi usado, por que foi usado e como adaptar para o seu PC. Se ajudar você, passe adiante. 🤝

---

## Índice

1. [Para quem é](#1-para-quem-é)
2. [Como usar com um agente de IA](#2-como-usar-com-um-agente-de-ia)
3. [Hardware de referência](#3-hardware-de-referência)
4. [Status dos testes](#4-status-dos-testes)
5. [O que tem nesta EFI](#5-o-que-tem-nesta-efi)
6. [O que você obrigatoriamente precisa trocar](#6-️-o-que-você-obrigatoriamente-precisa-trocar)
7. [Guia para o agente de IA (passo a passo)](#7-guia-para-o-agente-de-ia-passo-a-passo)
8. [Prompt pronto para colar no seu agente](#8-prompt-pronto-para-colar-no-seu-agente)
9. [BIOS](#9-bios)
10. [Kernel panic e solução de problemas](#10-kernel-panic-e-solução-de-problemas)
11. [Pós-instalação](#11-pós-instalação)
12. [Estrutura do repositório e scripts](#12-estrutura-do-repositório-e-scripts)
13. [Créditos, licenças e aviso](#13-créditos-licenças-e-aviso)

---

## 1. Para quem é

| Seu caso | Esta EFI serve? |
|---|---|
| **Mesmo hardware** (Ryzen 5 5500 + B450M Steel Legend + RX 6600) | Quase pronta. Você **precisa** gerar o seu SMBIOS e o ROM ([seção 6](#6-️-o-que-você-obrigatoriamente-precisa-trocar)) e, de preferência, conferir o mapa USB. |
| **AM4 parecido** (Ryzen 1000 a 5000, chipsets 300/400/500, GPU AMD suportada) | Sim, **como base**. Entregue este README ao seu agente de IA e siga a [seção 7](#7-guia-para-o-agente-de-ia-passo-a-passo). |
| AM5 (Ryzen 7000, Zen 4) | Só como referência. Há diferenças que este README não cobre; siga o Dortania e o AMD_Vanilla. |
| Ryzen 9000 (Zen 5, família 1Ah) | **Não.** O AMD_Vanilla só lista as famílias 15h, 16h, 17h e 19h. |
| Intel | **Não.** O processo é outro (outro guia do Dortania). |
| GPU **não suportada** no Sequoia (veja [7.3](#73-tabela-de-decisão-o-que-mudar-conforme-o-seu-hardware)) | **Não.** Sem GPU suportada não há aceleração gráfica, e em AMD não existe vídeo integrado utilizável. |

---

## 2. Como usar com um agente de IA

1. Baixe ou clone este repositório **no PC que vai rodar o macOS** (de preferência pelo Windows desse PC, porque o agente precisa ler o hardware).
2. Abra o seu agente de IA **na pasta do repositório**, com permissão para rodar comandos no terminal.
3. Cole o [prompt da seção 8](#8-prompt-pronto-para-colar-no-seu-agente).
4. O agente vai:
   1. levantar o seu hardware;
   2. comparar com a [seção 3](#3-hardware-de-referência);
   3. decidir o que mudar pela [tabela 7.3](#73-tabela-de-decisão-o-que-mudar-conforme-o-seu-hardware);
   4. regerar o que é específico de cada máquina (SSDTs, mapa USB, SMBIOS);
   5. validar com o `ocvalidate`;
   6. **só então**, com a sua confirmação, preparar o pendrive.

> Tudo aqui vem de fontes oficiais: [Dortania OpenCore Install Guide](https://dortania.github.io/OpenCore-Install-Guide/) (seção AMD "Zen"), [AMD_Vanilla](https://github.com/AMD-OSX/AMD_Vanilla) e as releases oficiais de cada projeto no GitHub. Se este README divergir do guia na versão atual do OpenCore, **o guia vence**.

---

## 3. Hardware de referência

| Componente | Modelo | IDs e caminhos (para comparação) |
|---|---|---|
| CPU | AMD Ryzen 5 5500, **6 núcleos / 12 threads** | Zen 3, die **Cezanne** (família de APU, com o vídeo integrado desativado), família 19h |
| Placa-mãe | ASRock B450M Steel Legend (chipset B450) | BIOS **P4.60** (10/2022) |
| GPU | AMD Radeon RX 6600 (Navi 23) | `1002:73FF`, nativa desde o macOS 12.1 |
| Áudio | Realtek **ALC897** | codec `10EC:0897`; controlador `1022:15E3` (ACPI `AZAL`) em `PciRoot(0x0)/Pci(0x8,0x1)/Pci(0x0,0x6)` |
| Ethernet | Realtek **RTL8111** (1 GbE) | `10EC:8168` em `PciRoot(0x0)/Pci(0x2,0x1)/Pci(0x0,0x2)/Pci(0x1,0x0)/Pci(0x0,0x0)` (ACPI `GPP3.PT02.PT21`) |
| USB | 3 controladores XHCI | `1022:1639` ×2 no CPU (`XHC0`, `XHC1`); `1022:43D5` no chipset (`PTXH`) |
| RAM | 32 GB DDR4 (2×16 GB) | rodando a 2667 MT/s, sem XMP |
| Armazenamento | SSD SATA (destino do macOS) + NVMe Silicon Motion SM2263 (Windows) | NVMe `126F:2263` |
| Wi-Fi / Bluetooth | Não tem Wi-Fi. Adaptador BT USB **Realtek** | Realtek BT **não funciona** no macOS |

---

## 4. Status dos testes

> Legenda: ✅ funciona · ⚠️ funciona com ressalva · ❌ não funciona · ⬜ ainda não testado
> Versão do macOS testada: **15.8 (24H23)**, instalada num SSD SATA Kingston A400, dando boot **sem o pendrive**.

| Item | Status | Observações |
|---|---|---|
| Boot do instalador (recovery) | ✅ | |
| Instalação completa | ✅ | macOS 15.8 (24H23) |
| 10 boots seguidos sem kernel panic | ⬜ | Nenhum pânico desde que o NVMeFix saiu (log: `Only 168/256 slide values are usable`, valor bom). Em 5 boots pelo SSD, **1 reiniciou sozinho** logo no começo do kernel, sem tela de pânico; o boot seguinte foi normal. Em observação |
| Aceleração gráfica (Metal) na RX 6600 | ✅ | `Metal 3`, 8 GB de VRAM |
| Vídeo pela HDMI e pela DisplayPort | ✅ | Dois monitores ao mesmo tempo (um na DP, outro na HDMI) |
| Áudio onboard (layout-id final: `11`) | ✅ | Layout 11 do AppleALC (`alc-layout-id = 11`) |
| Áudio pela HDMI/DP | ⬜ | Os dois monitores aparecem como saída de áudio; falta testar o som |
| Ethernet | ⚠️ | Link só com o meio **fixo em 100baseTX full-duplex**. Suspeita: cabo com par ruim (no Windows também só chega a 100 Mbps). Em teste com cabo novo |
| USB 2.0 / USB 3.0 / USB-C | ⬜ | |
| iCloud / App Store / iMessage / FaceTime | ⬜ | A `en0` já aparece como **Built-in** (`IOBuiltin = Yes`) |
| Sleep e wake | ⬜ | |
| Reiniciar e desligar | ⬜ | |
| NVRAM nativa | ⬜ | |
| Atualização OTA (com `revpatch=sbvmm`) | ⬜ | |
| Dual boot com o Windows | ✅ | O Windows (NVMe) dá boot pelo menu do OpenCore |
| Discord (chamada de voz) | ⚠️ | Travava ao entrar na call (Krisp usa Intel MKL). Funciona sem o Krisp: veja [11.1](#111-apps-que-travam-em-amd-intel-mkl) |
| Wi-Fi / Bluetooth / AirDrop / Handoff | ❌ | Não há hardware compatível (sem Wi-Fi; BT Realtek) |

> **Por que o `layout-id` aparece como 7?** No `ioreg`, o controlador de áudio (HDEF) mostra `layout-id = 7` mesmo com 11 no `config.plist`. Isso é normal: o AppleALC guarda o valor real em `alc-layout-id` e deixa 7 no `layout-id` para o AppleHDA aceitar. Confira com `ioreg -rd1 -n HDEF | grep layout`.

### Ajustes feitos depois dos testes

| Data | O que mudou | Por quê |
|---|---|---|
| 24/09/2026 | NVMeFix removido | Kernel panic no boot com NVMeFix no backtrace |
| 24/09/2026 | `enableEEE = false` no RealtekRTL8111; sem `npci`; Above 4G ligado | Ethernet sem link (`status: inactive`) |
| 25/09/2026 | Ethernet com o meio fixo em 100baseTX full-duplex (Ajustes do Sistema › Rede › Ethernet › Detalhes › Hardware) | No automático o link não subia. A causa provável é o cabo, não a EFI. ⏳ em teste com cabo novo |
| 25/09/2026 | `revpatch=sbvmm` no boot-args e `HideAuxiliary = True` | Pós-instalação: atualizações OTA no macOS 14.4+ e menu mais limpo (Espaço mostra a recovery) |

---

## 5. O que tem nesta EFI

### Versões

| Componente | Versão | Observação |
|---|---|---|
| OpenCorePkg | **1.0.7** | build **DEBUG** (para diagnóstico) |
| Lilu | 1.7.2 | |
| VirtualSMC | 1.3.7 | só o `VirtualSMC.kext` (os plugins SMCProcessor/SMCSuperIO são de Intel) |
| WhateverGreen | 1.7.0 | |
| AppleALC | 1.9.7 | |
| RestrictEvents | 1.1.6 | |
| RealtekRTL8111 | 3.0.0 | com **`enableEEE = false`** no Info.plist (veja [7.3](#73-tabela-de-decisão-o-que-mudar-conforme-o-seu-hardware)) |
| AppleMCEReporterDisabler | 1.2 | [link oficial citado pelo Dortania](https://github.com/acidanthera/bugtracker/files/3703498/AppleMCEReporterDisabler.kext.zip) |
| USBToolBox (kext) | 1.2.0 | + `UTBMap.kext` feito **para esta placa com este CPU** |
| HfsPlus.efi | OcBinaryData | |
| OpenCanopy.efi + `Resources` | OpenCore 1.0.7 + OcBinaryData | Picker gráfico, tema **GoldenGate** (sem a pasta `Audio`: não usamos o som no boot) |
| Patches AMD | AMD_Vanilla (commit `eaf52ef`) | core count ajustado para **6** |

### ACPI

| SSDT | Por quê |
|---|---|
| `SSDT-EC.aml` | O DSDT da B450M Steel Legend **não tem EC** (`PNP0C09`). É um EC falso sob `\_SB.PCI0.SBRG`, ativo só no macOS. |
| `SSDT-USBX.aml` | Propriedades de energia USB. Junto com o anterior, equivale ao `SSDT-EC-USBX` do Dortania. |

- Nenhum patch ou rename no DSDT.
- **Sem SSDT-CPUR:** nesta BIOS os CPUs estão declarados como `Processor`, e não como `Device (ACPI0007)`.
- As fontes `.dsl` estão em [`ACPI-fontes/`](ACPI-fontes/).

### Kexts (ordem de carregamento)

`Lilu` → `VirtualSMC` → `WhateverGreen` → `AppleALC` → `RestrictEvents` → `RealtekRTL8111` → `AppleMCEReporterDisabler` → `USBToolBox` → `UTBMap`

### Drivers UEFI

`OpenRuntime.efi`, `HfsPlus.efi`, `ResetNvramEntry.efi` e `OpenCanopy.efi` (picker gráfico).

### Configurações que diferem do `Sample.plist` 1.0.7

| Seção | Chave | Valor | Motivo |
|---|---|---|---|
| Booter › Quirks | EnableWriteUnprotector | **False** | Dortania Zen (conflita com RebuildAppleMemoryMap) |
| Booter › Quirks | RebuildAppleMemoryMap | **True** | Dortania Zen |
| Booter › Quirks | SyncRuntimePermissions | **True** | Dortania Zen |
| Booter › Quirks | SetupVirtualMap / ProvideCustomSlide / EnableSafeModeSlide / AvoidRuntimeDefrag | True | Padrão do guia para B450. Veja a [seção 10](#10-kernel-panic-e-solução-de-problemas) |
| Booter › Quirks | DevirtualiseMmio | False | Padrão (o guia só pede True em TRx40) |
| Booter › Quirks | ResizeAppleGpuBars | -1 | Resizable BAR desligado na BIOS |
| DeviceProperties | `layout-id` no controlador de áudio | `0B000000` (**11**) | ALC897. Alternativas para testar: 31, 12, 13 |
| DeviceProperties | `built-in` na Ethernet | `01` | Exigido pelo iCloud/App Store (en0 "built-in") |
| Kernel › Patch | AMD_Vanilla (25 patches) | core count `06` | Suporte a CPU AMD |
| Kernel › Emulate | DummyPowerManagement | **True** | AMD não tem gerenciamento de energia nativo |
| Kernel › Quirks | ProvideCurrentCpuInfo | **True** | Obrigatório para os patches AMD atuais |
| Kernel › Quirks | PanicNoKextDump / PowerTimeoutKernelPanic | **True** | Dortania Zen |
| Kernel › Quirks | XhciPortLimit | False | Não funciona no macOS 11.3+; o USB é resolvido pelo mapa |
| Misc › Boot | HideAuxiliary | **True** | Esconde a recovery e as ferramentas do menu. **Na instalação, aperte Espaço no menu do OpenCore** para mostrar a recovery do pendrive (ou mude para False) |
| Misc › Debug | AppleDebug / ApplePanic / DisableWatchDog | **True** | Diagnóstico |
| Misc › Debug | Target | **65** | Log **só em arquivo** (`opencore-*.txt` na raiz da partição EFI), sem texto na tela antes do picker. Com `67`, o log também aparece na tela |
| Misc › Boot | PickerMode / PickerVariant | **External** / **`Acidanthera\GoldenGate`** | Picker gráfico (OpenCanopy). Os outros temas também estão na EFI: `Acidanthera\Syrah` e `Acidanthera\Chardonnay`. Se faltar um arquivo do tema, o OpenCore volta sozinho para o menu de texto |
| Misc › Security | AllowSetDefault | **True** | |
| Misc › Security | ScanPolicy | **0** | |
| Misc › Security | SecureBootModel | **Disabled** | O guia manda `Disabled` do macOS 14.4 ao 26 (necessário para OTA) |
| Misc › Security | Vault | **Optional** | |
| NVRAM | boot-args | `-v keepsyms=1 debug=0x100 agdpmod=pikera revpatch=sbvmm` | Verbose; pânico fica na tela; `agdpmod=pikera` para GPU Navi; `revpatch=sbvmm` (RestrictEvents) libera as atualizações OTA no macOS 14.4+ |
| NVRAM | prev-lang:kbd | `pt-BR:128` | Português (Brasil) + teclado **ABNT2**. Americano: `en-US:0` |
| PlatformInfo | SystemProductName | **MacPro7,1** | Recomendado pelo Dortania para GPU AMD Polaris ou mais nova |
| PlatformInfo | Serial / MLB / UUID / ROM | **valores de exemplo** | ⚠️ gere os seus ([seção 6](#6-️-o-que-você-obrigatoriamente-precisa-trocar)) |

---

## 6. ⚠️ O que você obrigatoriamente precisa trocar

1. **SMBIOS** (`PlatformInfo › Generic`): `SystemSerialNumber`, `MLB` e `SystemUUID` estão com valores de exemplo. Gere os seus com o [GenSMBIOS](https://github.com/corpnewt/GenSMBIOS) para **MacPro7,1** e confira o serial em <https://checkcoverage.apple.com>. O resultado ideal é a Apple dizer que o **número de série não é válido**. **Nunca use o serial de outra pessoa** (nem de outro repositório): várias máquinas com a mesma identidade podem travar o iCloud de todo mundo.
2. **ROM**: coloque o **MAC da sua placa de rede** (en0), sem `:`. No Windows: `Get-NetAdapter -Physical | Select Name,PermanentAddress`.
3. **Mapa USB** (`UTBMap.kext`): feito para **esta placa com um Ryzen Cezanne**. Mesmo com a mesma placa, um CPU diferente (por exemplo, um 5600X, que é Vermeer) tem outros controladores USB no processador. **Refaça** ([7.5](#75-mapa-usb)).
4. **Caminhos de dispositivo** (`DeviceProperties`): o do áudio e o da Ethernet mudam conforme o CPU e a placa. Confira os seus ([7.6](#76-áudio) e [7.7](#77-rede-e-icloud)).
5. **SSDTs**: se a sua placa não for a B450M Steel Legend, regere com o SSDTTime ([7.4](#74-ssdts)).
6. **Core count**: se o seu CPU não tem 6 núcleos, ajuste os 4 patches ([7.3](#73-tabela-de-decisão-o-que-mudar-conforme-o-seu-hardware)).

> 🔒 **Ao publicar a SUA versão:** nunca suba o seu serial, MLB, UUID nem o ROM (MAC). Também não suba a recovery da Apple (`com.apple.recovery.boot`) nem os logs do OpenCore, que podem conter esses dados.

---

## 7. Guia para o agente de IA (passo a passo)

### 7.1 Regras de segurança (obrigatórias)

1. **Nunca formatar, particionar nem escrever em discos internos.** Só mexa no pendrive.
2. Antes de formatar o pendrive: **liste os discos, mostre modelo, tamanho, número de série e letra, e espere a confirmação explícita do usuário.** Identifique o pendrive pelo **número de série**, não pelo número do disco (que muda quando se pluga outra coisa).
3. Não alterar configurações do Windows, drivers ou BIOS. As mudanças de BIOS o usuário faz pela [seção 9](#9-bios).
4. Baixar **somente** das releases oficiais no GitHub (acidanthera, AMD-OSX, corpnewt, USBToolBox, Mieze etc.). **Nada de EFIs prontas de terceiros.**
5. Usar o `ocvalidate` **da mesma versão** do OpenCore.
6. Explicar ao usuário **cada** divergência em relação a este README e ao guia do Dortania.
7. Nunca expor nem publicar o SMBIOS/ROM do usuário.

### 7.2 Levantar o hardware (Windows / PowerShell)

```powershell
Get-CimInstance Win32_Processor | Select Name,NumberOfCores,NumberOfLogicalProcessors
Get-CimInstance Win32_BaseBoard | Select Manufacturer,Product
Get-CimInstance Win32_BIOS | Select SMBIOSBIOSVersion,ReleaseDate
Get-CimInstance Win32_VideoController | Select Name,PNPDeviceID
# Codec de audio: o DEV_xxxx de HDAUDIO\FUNC_01&VEN_10EC&DEV_xxxx identifica o codec Realtek
Get-CimInstance Win32_PnPEntity | ? { $_.PNPDeviceID -like 'HDAUDIO*' } | Select Name,PNPDeviceID
Get-CimInstance Win32_PnPEntity | ? { $_.PNPClass -eq 'Net' -and $_.PNPDeviceID -like 'PCI*' } | Select Name,PNPDeviceID
Get-Disk | Select Number,FriendlyName,BusType,Size
# Caminho PCI de um dispositivo (para DeviceProperties):
Get-PnpDeviceProperty -InstanceId '<InstanceId>' -KeyName DEVPKEY_Device_LocationPaths | Select -Expand Data
```

**Conversão de caminho:** o Windows mostra `PCIROOT(0)#PCI(0801)#PCI(0006)`. Em cada `PCI(DDFF)`, `DD` é o dispositivo e `FF` a função, em hexadecimal. Então esse exemplo vira `PciRoot(0x0)/Pci(0x8,0x1)/Pci(0x0,0x6)`.

No Linux, os equivalentes são `lspci -nn`, `cat /proc/asound/card*/codec#* | grep Codec` e `lsusb -t`.

### 7.3 Tabela de decisão (o que mudar conforme o seu hardware)

| Se o seu hardware… | Faça isto |
|---|---|
| **CPU com outro número de núcleos** | Nos 4 patches `algrey - Force cpuid_cores_per_package`, troque **só o 2º byte** do `Replace` pelo nº de **núcleos físicos** em hex (4→`04`, 6→`06`, 8→`08`, 12→`0C`, 16→`10`). O do Sequoia é o `BA<nn>000000`. Core count errado causa kernel panic. |
| **Ryzen Vermeer/Matisse** (5600X, 5800X, 3600…) em vez de Cezanne (5500, 5600G, 5700G…) | Os controladores USB do CPU e o caminho do áudio mudam: **refaça o mapa USB** e leia de novo o caminho do áudio. |
| **Chipset B550 ou A520** | Veja se os CPUs são `Device (ACPI0007)` no DSDT/SSDT. Se forem, entra o **SSDT-CPUR** (do Dortania). O guia também manda **`SetupVirtualMap = False`**. |
| **X570** | Pode precisar de `SetupVirtualMap = False` (nota do guia). |
| **B450/X470 com BIOS de fim de 2020 em diante** | O guia avisa que **pode precisar de `SetupVirtualMap = False`**. Esta EFI está com True; é o 1º teste se o boot travar cedo. |
| **B350/X370/A320** | Igual a esta EFI (sem CPUR), mas regere as SSDTs. |
| **GPU RX 5500/5600/5700 (Navi 10/14), RX 6600/6600 XT (Navi 23), RX 6800/6800 XT/6900 XT (Navi 21)** | Mantém `agdpmod=pikera`. |
| **GPU Polaris (RX 460 a 590) ou Vega** | **Remova** `agdpmod=pikera` (é só para Navi). |
| **GPU RX 6700/6700 XT/6750 XT (Navi 22), RX 6400/6500 XT (Navi 24), RX 7000+, NVIDIA atual, Intel Arc** | **Não suportada** no Sequoia. Para variantes específicas (6650 XT, 6950 XT…), confira o [GPU Buyers Guide do Dortania](https://dortania.github.io/GPU-Buyers-Guide/). |
| **Codec de áudio diferente** | Escolha o `layout-id` ([7.6](#76-áudio)). |
| **Ethernet Realtek RTL8111 sem link** (`ifconfig en0` → `status: inactive`) | Desligue o EEE: `enableEEE` = `false` em `RealtekRTL8111.kext/Contents/Info.plist` › *Driver Parameters* (opção documentada pelo autor). **Não use `npci=0x2000/0x3000`** (o README do driver manda evitar). Teste o meio manual no Terminal: `ifconfig en0 media 100baseTX mediaopt full-duplex`. Se só funcionar assim, desconfie do **cabo** antes da EFI (foi o caso aqui: no Windows o link também não passava de 100 Mbps). |
| **Ethernet Realtek RTL8125 (2.5 GbE)** | Troque RealtekRTL8111 por **LucyRTL8125Ethernet**. |
| **Ethernet Intel (I211, I225…) ou outra** | Veja a seção Ethernet do [guia de kexts do Dortania](https://dortania.github.io/OpenCore-Install-Guide/ktext.html). |
| **NVMe na máquina** | O **NVMeFix** é opcional. **Aqui ele causou kernel panic no boot** (`org.acidanthera.NVMeFix` no backtrace) com um NVMe Silicon Motion SM2263 e foi **removido**. Só inclua se o macOS for instalado no NVMe, e teste. |
| **NVMe Samsung PM981/PM991 ou Micron 2200S** | Incompatíveis (Anti-Hardware Buyers Guide). Não instale neles e prefira desativá-los. |
| **Wi-Fi/Bluetooth** | Esta EFI não tem nenhum kext para isso. Veja o guia de kexts do Dortania para o seu chip. |
| **Teclado não ABNT2** | `prev-lang:kbd`: `en-US:0` (americano) ou vazio, para o instalador perguntar. |

### 7.4 SSDTs

1. Use o [SSDTTime](https://github.com/corpnewt/SSDTTime): opção **P** (dump das tabelas da máquina), depois **2** (FakeEC) e **4** (USBX).
2. Confira a declaração dos CPUs no ACPI descompilado. Procure por `Processor (` versus `ACPI0007`. Se for `ACPI0007`, precisa do **SSDT-CPUR**.
3. Se o SSDTTime sugerir outra coisa, **explique ao usuário o motivo** antes de incluir.
4. Os `.aml` vão em `EFI/OC/ACPI/`, e as entradas em `ACPI › Add`.

### 7.5 Mapa USB

- Ferramenta oficial: [USBToolBox](https://github.com/USBToolBox/tool) (`Windows.exe`), fazendo **Discover Ports** e depois **Select Ports and Build Kext**.
- Limite de **15 portas por controlador**, contando o lado USB 2 e o lado USB 3 de cada porta como portas separadas.
- Teste **cada porta física** com um dispositivo **USB 3.0 de verdade** e um **USB 2.0**. O **USB-C** tem que ser testado **dos dois lados**.
- ⚠️ **Bug encontrado nesta máquina:** com o **Parsec Virtual USB Adapter** instalado (o Parsec é um app de acesso remoto), o `usbdump` do USBToolBox 0.2 **trocou os barramentos PCI dos controladores e omitiu um deles (o XHC0)**. Se o USBToolBox listar menos controladores XHCI do que o Gerenciador de Dispositivos, use os scripts deste repositório:
  - `python scripts/usb_ports.py`: fotografia das portas (somente leitura; mesmas consultas do USBView da Microsoft; detecta sozinho os controladores XHCI reais e ignora os virtuais).
  - `python scripts/usb_ports.py --watch`: registra em `usb-descoberta.json` tudo que for plugado em cada porta.
  - `python scripts/build_usbmap.py`: gera o `UTBMap.kext` no mesmo formato do USBToolBox (inclui as portas que o firmware declara como conectáveis; ajuste `TYPE_OVERRIDES` para a USB-C = tipo `10`).
- Tipos (`UsbConnector`): `0` = USB 2 Type-A, `3` = USB 3 Type-A, `9` = Type-C só USB 2, `10` = Type-C com switch, `255` = interna.
- **Sem mapa ainda?** Use `USBToolBox.kext` + `UTBDefault.kext` (fluxo oficial para instalar antes de mapear) e mapeie depois.

### 7.6 Áudio

1. Descubra o codec: é o `DEV_xxxx` do `HDAUDIO\FUNC_01&VEN_10EC&DEV_xxxx`.
2. Veja os layouts disponíveis em `Resources/ALCxxx/Info.plist` do [AppleALC](https://github.com/acidanthera/AppleALC) e na lista de [codecs suportados](https://github.com/acidanthera/AppleALC/wiki/Supported-codecs).
3. **Método usado aqui para escolher:** decodificar os pin configs de cada layout (`Resources/PinConfigs.kext` → `HDAConfigDefault`, filtrando pelo `CodecID`) e escolher o que tem os mesmos conectores do painel da placa. Por exemplo: saída verde atrás, mic rosa, line-in azul, fone e mic na frente.
4. Para testar rápido, adicione `alcid=N` ao `boot-args` (tem prioridade). O valor final vai em `DeviceProperties › <caminho do controlador de áudio> › layout-id` (Data, 4 bytes little-endian: 11 → `0B000000`).
5. O `boot-args` é regravado pelo OpenCore a cada boot. Mude no `config.plist`, não pelo `nvram` do macOS.

### 7.7 Rede e iCloud

- `ROM` = MAC da en0, sem `:`.
- `DeviceProperties › <caminho da Ethernet> › built-in` = Data `01`.
- Isso só funciona se **todas as pontes PCI até o dispositivo existirem no ACPI**. No Windows, o `DEVPKEY_Device_LocationPaths` tem uma forma `ACPI(...)#ACPI(...)#...`: se aparecer `PCI(xxxx)` **antes** do próprio dispositivo, falta uma ponte, e ela é criada com o SSDTTime (opção **9, PCI Bridge**).
- O Apple ID importa: conta nova sem nenhum aparelho Apple costuma ser bloqueada no primeiro login.

### 7.8 SMBIOS

Siga o GenSMBIOS com **MacPro7,1**, depois o checkcoverage (resultado "não válido"). Grave em `smbios-gerado.txt` (modelo: `smbios-gerado.exemplo.txt`). **Nunca versione esse arquivo.**

### 7.9 Gerar e validar o `config.plist`

- **Opção A (ProperTree):** edite `EFI/OC/config.plist` à mão no [ProperTree](https://github.com/corpnewt/ProperTree) e use **OC Snapshot (Clean)** depois de adicionar ou remover kexts.
- **Opção B (script):** `scripts/build_config.py` regenera o config a partir do `Sample.plist` do OpenCore e do `patches.plist` do AMD_Vanilla.
  - Constantes no topo: `CORE_COUNT`, `LAYOUT_ID`, `HDEF_PATH`, `LAN_PATH` e `KEXT_ORDER`.
  - Caminhos esperados: `downloads/x/OpenCore-1.0.7-DEBUG/Docs/Sample.plist` e `tools/AMD_Vanilla/patches.plist`.
  - Lê o SMBIOS de `smbios-gerado.txt`.
- **Sempre** rode: `Utilities/ocvalidate/ocvalidate.exe EFI/OC/config.plist`, com a **mesma versão** do OpenCore. O esperado é `No issues found`.

### 7.10 Pendrive (Windows)

1. **Recovery do Sequoia**, com o comando do Dortania, em `Utilities/macrecovery` do OpenCore:
   ```
   py macrecovery.py -b Mac-937A206F2EE63C01 -m 00000000000000000 download
   ```
   Se rodar sem um console de verdade (por exemplo, em segundo plano por um agente), o script quebra em `os.get_terminal_size()`. Rode num terminal normal.
2. **Formatar:** pendrive de ≥ 16 GB, **GPT + partição FAT32**. O Windows não formata FAT32 acima de 32 GB, então uma partição de 16 GB basta. O script `scripts/preparar-pendrive.ps1 -Serial <serial> -TamanhoGB <tamanho>` confere o serial, o barramento USB e o tamanho antes de apagar. Precisa rodar como administrador.
3. Copie para a raiz do pendrive: a pasta `EFI` e a pasta `com.apple.recovery.boot` (com `BaseSystem.dmg` e `.chunklist`).

---

## 8. Prompt pronto para colar no seu agente

```text
Você vai me ajudar a adaptar a EFI OpenCore deste repositório para o MEU hardware, para instalar
o macOS Sequoia. Antes de qualquer coisa, leia o README.md inteiro deste repositório.

Regras (obrigatórias):
- Siga a seção 7.1 do README (segurança). NUNCA escreva em discos internos. Antes de formatar o
  pendrive, liste os discos, mostre modelo/tamanho/serial/letra e ESPERE minha confirmação.
- Fonte de verdade: guia Dortania (seção AMD Zen) e AMD_Vanilla. Se o README divergir do guia
  atual, siga o guia e me avise da diferença.
- Baixe só releases oficiais do GitHub. Nada de EFIs prontas de terceiros.
- Não altere configurações do Windows, drivers nem BIOS (a BIOS eu ajusto sozinho pela seção 9).
- Meu SMBIOS/ROM nunca pode ir para lugar público.

Tarefas:
1. Levante meu hardware (seção 7.2) e grave num arquivo hardware.txt.
2. Compare com a seção 3 e me mostre uma tabela: "igual" / "diferente" / "o que muda" (use a tabela 7.3).
3. Baixe a versão atual do OpenCore (DEBUG) e dos kexts necessários, e o ocvalidate da mesma versão.
4. Regere as SSDTs com o SSDTTime (7.4) e me explique cada uma.
5. Faça o mapa USB (7.5); me diga quando e em quais portas plugar os dispositivos.
6. Descubra meu codec de áudio e escolha o layout-id, com 2 ou 3 alternativas (7.6).
7. Ajuste rede/iCloud (7.7) e gere meu SMBIOS MacPro7,1 (7.8). Eu confiro o serial no site da Apple.
8. Gere o config.plist (7.9), rode o ocvalidate e corrija tudo.
9. Me explique cada quirk que você mudou em relação a este README.
10. Só depois, com a minha confirmação, prepare o pendrive (7.10).
No final, escreva um README-EFI.md com versões, SSDTs, quirks alterados, layout-ids alternativos e pendências.
```

---

## 9. BIOS

Estes são os itens do Dortania para AMD. Os caminhos são os do **manual da ASRock B450M Steel Legend**; em outras placas os nomes mudam, mas as opções são as mesmas. Tire foto das telas antes de mexer.

| Ordem | Opção | Onde fica (ASRock) | Valor |
|---|---|---|---|
| 1 | Fast Boot | Boot › Fast Boot | **Disabled** (faça primeiro: pode esconder o menu do CSM) |
| 2 | CSM | Boot › CSM (Compatibility Support Module) › CSM | **Disabled** |
| 3 | Above 4G Decoding | Boot › Above 4G Decoding | **Enabled** |
| 4 | Re-Size BAR | logo abaixo do Above 4G (se existir) | **Disabled** |
| 5 | Secure Boot | Security › Secure Boot | **Disabled** |
| 6 | IOMMU | Advanced › AMD CBS › NBIO Common Options › NB Configuration › IOMMU | **Disabled** |
| 7 | Porta serial | Advanced › Super IO Configuration › Serial Port | **Disabled** |
| 8 | SATA Mode | Advanced › Storage Configuration › SATA Mode | **AHCI** |
| 9 | XHCI Hand-off | (não existe nesta placa) | Enabled, se existir |
| 10 | XMP | OC Tweaker (perfil de memória) | **desligado** no 1º teste |
| n/a | Global C-state Control | Advanced › AMD CBS › Zen (ou CPU) Common Options | só desligue se os pânicos continuarem |

- **ASRock e Gigabyte:** o guia avisa que ligar o **Above 4G pode quebrar a Ethernet** e sugere `npci=0x3000` no lugar. **Nesta placa isso não resolveu**, e o README do RealtekRTL8111 manda **evitar `npci`**. Aqui a Ethernet sem link foi tratada desligando o EEE do driver e fixando o meio em 100baseTX full-duplex. A causa provável era o cabo (veja [7.3](#73-tabela-de-decisão-o-que-mudar-conforme-o-seu-hardware)).
- Menu de boot da ASRock: **F11**. Setup: **F2** ou **Del**.

---

## 10. Kernel panic e solução de problemas

### Por que o pânico é "intermitente" (às vezes liga, às vezes não)

A cada boot, o kernel do macOS é carregado num **endereço aleatório** (KASLR, 256 posições possíveis). No PC, parte dessa memória está ocupada pelo firmware. Quando o sorteio cai numa posição ocupada, o boot falha. Como o sorteio muda a cada boot, o problema aparece **só às vezes**.

| Quirk | O que faz |
|---|---|
| `ProvideCustomSlide = True` | O OpenCore calcula os endereços livres e só sorteia entre eles. No log DEBUG: `OCABC: Only N/256 slide values are usable!` = necessário (N baixo é suspeito); `All slides are usable!` = o problema não é esse. |
| `EnableSafeModeSlide = True` | Vale também no modo seguro (`-x`). |
| `DevirtualiseMmio` | True libera memória do firmware e **aumenta os endereços válidos**. É o próximo passo se N for baixo. Pode exigir `MmioWhitelist`. |
| `SetupVirtualMap` | Corrige chamadas do firmware AMI. **B450/X470 com BIOS de fim de 2020 em diante pode precisar de False.** |

**Ordem de testes** (uma mudança por vez, sempre lendo o log):

1. `SetupVirtualMap = False`
2. Se o log mostrar poucos slides: `DevirtualiseMmio = True`
3. Se travar em `[EB|#LOG:EXITBS:START]`: `EnableWriteUnprotector = True` + `RebuildAppleMemoryMap = False`

### Como ler o pânico

- **Tire foto da tela.** Com `keepsyms=1 debug=0x100`, o pânico fica parado e mostra o nome do kext ou da função.
- O log do OpenCore fica em `opencore-AAAA-MM-DD-HHMMSS.txt`, na raiz do pendrive (abre no Windows).

| Aparece no pânico | Suspeito |
|---|---|
| `AppleIntelMCEReporter` | Falta o AppleMCEReporterDisabler, ou ele não carregou |
| `non-monotonic time` | Os patches "Visual" do AMD_Vanilla estão desativados |
| `org.acidanthera.NVMeFix` / `IONVMeFamily` | Remova o NVMeFix (foi o caso desta máquina). Se continuar, o SSD NVMe pode ser incompatível: desative-o |
| `XHCI` / USB | Mapa USB errado ou faltando |
| Pânico logo no começo, sem texto do kernel | Quirks de Booter (ordem de testes acima) |
| Tela preta depois de carregar | `agdpmod=pikera` (Navi); teste outra saída (DP × HDMI) |
| Core count / `cpuid` | Patch de core count com o número errado |

Outras dicas:
- XMP desligado no primeiro teste.
- Se nada resolver, teste com Global C-state Control desligado.

---

## 11. Pós-instalação

1. Copie a `EFI` do pendrive para a partição EFI do disco do macOS.
2. **Atualizações OTA (macOS 14.4+):** o `revpatch=sbvmm` já está no boot-args desta EFI (precisa do RestrictEvents, que já está incluído). Mantenha `SecureBootModel = Disabled`. Não dá para conferir com o `sysctl kern.hv_vmm_present` no Terminal: o RestrictEvents só responde `1` para o `softwareupdated` e o `osinstallersetupd`, então no Terminal o normal é `0`. O teste é o Atualização de Software procurar e oferecer atualizações sem erro.
3. Confira no Hackintool (System › Peripherals) se a `en0` aparece com **Built-in**.
4. Faça o primeiro login no iCloud pela Ethernet.
5. Teste se a NVRAM funciona (seção "Verifying NVRAM" do [guia de iServices](https://dortania.github.io/OpenCore-Post-Install/universal/iservices.html)).
6. Com o sistema estável, você pode:
   - trocar o OpenCore para a build RELEASE (todos os `.efi`, inclusive o `OpenCanopy.efi`);
   - desligar os logs (`Target = 3`, `AppleDebug` e `ApplePanic = False`) e apagar os `opencore-*.txt` da partição EFI;
   - o verbose (`-v`) pode ficar, se você gosta de ver o boot.

### 11.1 Apps que travam em AMD (Intel MKL)

Alguns apps usam a **Intel MKL** (Math Kernel Library), que no macOS só funciona em CPU Intel e **fecha o app** em Ryzen. O problema é do processador AMD, não do Sequoia. A [FAQ do AMD-OSX](https://github.com/AMD-OSX/AMD-OSX-FAQ/blob/main/faq.txt) cita, entre outros: Adobe CC, Discord (Krisp), MATLAB, Autodesk Maya/AutoCAD e plugins Waves. Para ver se um app seu usa a MKL:

```bash
grep -rlaF mkl_serv_intel_cpu_true /Applications ~/Library/Application\ Support 2>/dev/null
```

**Discord** (testado na versão 0.0.413, em 25/09/2026): fechava na hora de entrar numa chamada de voz. Quem usa a MKL é o **Krisp**, e o `~/Library/Application Support/discord/logs/discord_krisp.log` para logo depois de `KrispVADSetup` ou de `Setting Krisp model`. A solução, sem patch nenhum, é em **Configurações do Usuário › Voz e Vídeo**:

1. **Perfil de entrada:** **Personalizado**. O perfil **Isolamento de Voz** usa o Krisp.
2. **Supressão de ruído:** **Padrão** (WebRTC, sem MKL), em vez de Krisp.
3. **Desligue "Ajustar Automaticamente a Sensibilidade de Entrada".** Nesta versão, ela usa o VAD do Krisp: só trocar a supressão de ruído **não** resolve.
4. **Ajuste o slider de sensibilidade à mão:** o teclado e o ventilador ficam abaixo da bolinha (amarelo), e a voz passa dela (verde). Com o slider todo à esquerda, o Discord transmite o tempo todo e pega teclado e vento. Baixar o ganho do microfone e chegar mais perto ajuda muito.

> **Por que não o patch?** As correções antigas só definem a variável `MKL_DEBUG_CPU_TYPE=5`, e a oneAPI MKL do Krisp atual ignora essa variável. O patch no binário (AMDFriend) funciona, mas o Discord só carrega bibliotecas com a assinatura dele: o Krisp modificado só carrega com o **SIP desligado**. Não recomendo trocar a segurança do sistema por uma supressão de ruído.

**Photoshop/Adobe:** não testado nesta máquina. Veja a FAQ do AMD-OSX e o [AMDFriend](https://codeberg.org/NyaomiDEV/AMDFriend).

### 11.2 Apps recomendados (opcionais)

| App | Para quê | Observações |
|---|---|---|
| [**Mos**](https://mos.caldis.me/) ([GitHub](https://github.com/Caldis/Mos)) | **Rolagem suave** para mouse comum. No macOS, a roda de um mouse USB rola aos "trancos", linha por linha; o Mos suaviza. Também separa a direção da rolagem do mouse da do trackpad | Gratuito e de código aberto; a release oficial é assinada e **notarizada** pela Apple. Testado: 4.2.1. Baixe o `.zip` da página oficial, arraste o `Mos.app` para **Aplicativos** e, na primeira vez, permita em **Ajustes do Sistema › Privacidade e Segurança › Acessibilidade**. Para abrir sozinho: *Iniciar no login*, nas preferências do Mos |
| [**Hackintool**](https://github.com/benbaker76/Hackintool) | Conferir PCI, USB, `en0` Built-in e NVRAM | Usado nos passos de pós-instalação acima |

---

## 12. Estrutura do repositório e scripts

```
EFI/                          EFI pronta (SMBIOS com valores de exemplo)
  BOOT/BOOTx64.efi
  OC/ ACPI/ Drivers/ Kexts/ Tools/ Resources/ OpenCore.efi config.plist
ACPI-fontes/                  SSDT-EC.dsl e SSDT-USBX.dsl (para leitura)
scripts/
  build_config.py             gera o config.plist (Sample.plist + AMD_Vanilla + constantes)
  usb_ports.py                lê as portas USB dos controladores XHCI (somente leitura)
  build_usbmap.py             gera o UTBMap.kext no formato do USBToolBox
  preparar-pendrive.ps1       formata SÓ o pendrive (confere serial/USB/tamanho)
smbios-gerado.exemplo.txt     modelo do arquivo com SEU serial/MLB/UUID/ROM (não versionar o real)
```

A recovery da Apple **não** está incluída. Baixe com o `macrecovery.py` ([7.10](#710-pendrive-windows)).

---

## 13. Créditos, licenças e aviso

- **[Acidanthera](https://github.com/acidanthera):** OpenCore, Lilu, VirtualSMC, WhateverGreen, AppleALC, RestrictEvents, NVMeFix, OcBinaryData
- **[AMD-OSX / AMD_Vanilla](https://github.com/AMD-OSX/AMD_Vanilla):** patches do kernel para AMD
- **[Mieze](https://github.com/Mieze/RTL8111_driver_for_OS_X):** RealtekRTL8111
- **XLNC:** AppleMCEReporterDisabler
- **[USBToolBox](https://github.com/USBToolBox):** kext e ferramenta de mapeamento
- **[CorpNewt](https://github.com/corpnewt):** SSDTTime, ProperTree, GenSMBIOS
- **[Dortania](https://dortania.github.io/):** guias de instalação e pós-instalação

Cada binário mantém a licença do seu projeto de origem. Esta EFI foi montada com a ajuda de um agente de IA (Claude Code), seguindo somente as fontes acima, e testada no hardware da [seção 3](#3-hardware-de-referência).

**Aviso:** material para fins educacionais. A licença do macOS da Apple só permite instalá-lo em hardware da Apple; a responsabilidade pelo uso é sua. Sem garantia: faça backup antes de mexer em discos.
