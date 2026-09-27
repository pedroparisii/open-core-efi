<#
  FASE 1 - Inventario de hardware para EFI OpenCore (SOMENTE LEITURA).
  Nao altera nada no sistema: apenas consulta WMI/CIM, PnP, discos e firmware.
  Identificadores pessoais (serial da placa/BIOS/disco, UUID, MAC) NAO sao coletados.

  Uso (PowerShell como Administrador, para ler Secure Boot e bcdedit):
    Set-ExecutionPolicy -Scope Process Bypass
    .\inventario.ps1
  Gera .\inventario-<data>.json
#>
$ErrorActionPreference = 'SilentlyContinue'
$stamp = Get-Date -Format 'yyyyMMdd-HHmm'
$json  = Join-Path $PSScriptRoot "inventario-$stamp.json"
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

$pnp = Get-PnpDevice -PresentOnly | Select-Object Class, FriendlyName, InstanceId, Status

function DevProp($id, $key) {
  (Get-PnpDeviceProperty -InstanceId $id -KeyName $key).Data
}

$r = [ordered]@{}
$r.RunAsAdmin = $isAdmin

# --- Sistema / firmware ---
$os = Get-CimInstance Win32_OperatingSystem
$cv = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
$r.Windows = [ordered]@{
  Caption = $os.Caption; Version = $os.Version; DisplayVersion = $cv.DisplayVersion
  Build = "$($cv.CurrentBuildNumber).$($cv.UBR)"; Arch = $os.OSArchitecture
}
$r.BootMode = $env:firmware_type   # UEFI ou Legacy
$r.SecureBoot = if ($isAdmin) { try { Confirm-SecureBootUEFI } catch { "indisponivel: $($_.Exception.Message)" } } else { 'rode como Admin' }
$r.SecureBootStateReg = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\SecureBoot\State').UEFISecureBootEnabled
$r.BcdCurrent = if ($isAdmin) { (bcdedit /enum '{current}') -join "`n" } else { 'rode como Admin' }
$dg = Get-CimInstance -Namespace root\Microsoft\Windows\DeviceGuard -ClassName Win32_DeviceGuard
$r.VBS = [ordered]@{ VirtualizationBasedSecurityStatus = $dg.VirtualizationBasedSecurityStatus; SecurityServicesRunning = $dg.SecurityServicesRunning }
$r.FastStartup = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Power').HiberbootEnabled
$r.RealTimeIsUniversal = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\TimeZoneInformation').RealTimeIsUniversal

# --- CPU / placa / BIOS / RAM ---
$cpu = Get-CimInstance Win32_Processor
$r.CPU = [ordered]@{ Name = $cpu.Name.Trim(); ProcessorId = $cpu.ProcessorId; Cores = $cpu.NumberOfCores
  Threads = $cpu.NumberOfLogicalProcessors; MaxClockMHz = $cpu.MaxClockSpeed; Virtualization = $cpu.VirtualizationFirmwareEnabled }
$bb = Get-CimInstance Win32_BaseBoard
$r.Motherboard = [ordered]@{ Manufacturer = $bb.Manufacturer; Product = $bb.Product; Version = $bb.Version }
$bios = Get-CimInstance Win32_BIOS
$r.BIOS = [ordered]@{ Vendor = $bios.Manufacturer; Version = $bios.SMBIOSBIOSVersion; Date = $bios.ReleaseDate
  SMBIOSVersion = "$($bios.SMBIOSMajorVersion).$($bios.SMBIOSMinorVersion)" }
$r.RAM = @(Get-CimInstance Win32_PhysicalMemory | ForEach-Object {
  [ordered]@{ Slot = $_.DeviceLocator; SizeGB = [math]::Round($_.Capacity/1GB); SpeedMHz = $_.Speed
    ConfiguredMHz = $_.ConfiguredClockSpeed; Manufacturer = $_.Manufacturer; PartNumber = "$($_.PartNumber)".Trim() } })

# --- GPU ---
$r.GPU = @(Get-CimInstance Win32_VideoController | ForEach-Object {
  [ordered]@{ Name = $_.Name; PNPDeviceID = $_.PNPDeviceID; DriverVersion = $_.DriverVersion
    Location = (DevProp $_.PNPDeviceID 'DEVPKEY_Device_LocationInfo') } })

# --- Todos os dispositivos PCI com localizacao (para device path / USB mapping) ---
$r.PCI = @($pnp | Where-Object InstanceId -like 'PCI\*' | ForEach-Object {
  [ordered]@{ Class = $_.Class; Name = $_.FriendlyName; InstanceId = $_.InstanceId
    Location = (DevProp $_.InstanceId 'DEVPKEY_Device_LocationInfo')
    LocationPaths = (DevProp $_.InstanceId 'DEVPKEY_Device_LocationPaths')
    Driver = (DevProp $_.InstanceId 'DEVPKEY_Device_DriverDesc') } })

# --- Audio: codec HDA (VEN/DEV do codec) ---
$r.AudioCodecs = @($pnp | Where-Object { $_.InstanceId -like 'HDAUDIO\*' } | ForEach-Object {
  [ordered]@{ Name = $_.FriendlyName; InstanceId = $_.InstanceId } })

# --- Rede (sem MAC) ---
$r.Network = @(Get-NetAdapter -IncludeHidden | Where-Object { $_.PnPDeviceID -like 'PCI\*' -or $_.PnPDeviceID -like 'USB\*' } | ForEach-Object {
  [ordered]@{ Name = $_.Name; Description = $_.InterfaceDescription; PnPDeviceID = $_.PnPDeviceID
    Status = "$($_.Status)"; LinkSpeed = $_.LinkSpeed; DriverVersion = $_.DriverVersion } })

# --- USB: controladores, hubs e dispositivos (inclui procura por VID_368B&PID_8D81) ---
$r.USBControllers = @($pnp | Where-Object Class -eq 'USB' | Where-Object InstanceId -like 'PCI\*' | ForEach-Object {
  [ordered]@{ Name = $_.FriendlyName; InstanceId = $_.InstanceId } })
$r.USBDevices = @($pnp | Where-Object InstanceId -match '^USB\\VID_' | ForEach-Object {
  [ordered]@{ Class = $_.Class; Name = $_.FriendlyName; InstanceId = $_.InstanceId
    LocationInfo = (DevProp $_.InstanceId 'DEVPKEY_Device_LocationInfo')
    Parent = (DevProp $_.InstanceId 'DEVPKEY_Device_Parent') } })
$r.Device_368B_8D81 = @($pnp | Where-Object InstanceId -match 'VID_368B&PID_8D81' | ForEach-Object {
  [ordered]@{ Class = $_.Class; Name = $_.FriendlyName; InstanceId = $_.InstanceId; Status = $_.Status } })

# --- Armazenamento (sem numero de serie) ---
$r.PhysicalDisks = @(Get-PhysicalDisk | ForEach-Object {
  [ordered]@{ DeviceId = $_.DeviceId; Model = $_.FriendlyName; Bus = "$($_.BusType)"; Media = "$($_.MediaType)"
    SizeGB = [math]::Round($_.Size/1GB); Firmware = $_.FirmwareVersion } })
$r.Disks = @(Get-Disk | ForEach-Object {
  [ordered]@{ Number = $_.Number; Model = $_.FriendlyName; PartitionStyle = "$($_.PartitionStyle)"
    IsBoot = $_.IsBoot; IsSystem = $_.IsSystem; SizeGB = [math]::Round($_.Size/1GB) } })
$r.Partitions = @(Get-Partition | ForEach-Object {
  [ordered]@{ Disk = $_.DiskNumber; Part = $_.PartitionNumber; Type = "$($_.Type)"; GptType = $_.GptType
    Letter = "$($_.DriveLetter)"; SizeGB = [math]::Round($_.Size/1GB,2) } })
$r.Volumes = @(Get-Volume | ForEach-Object {
  [ordered]@{ Letter = "$($_.DriveLetter)"; Label = $_.FileSystemLabel; FS = $_.FileSystem; SizeGB = [math]::Round($_.Size/1GB,2) } })
$r.StorageControllers = @($pnp | Where-Object { $_.Class -in 'SCSIAdapter','HDC' } | ForEach-Object {
  [ordered]@{ Class = $_.Class; Name = $_.FriendlyName; InstanceId = $_.InstanceId } })

# --- ACPI: dispositivos relevantes (EC, RTC, PMC, LPC, etc.) ---
$r.ACPI = @($pnp | Where-Object InstanceId -like 'ACPI\*' | ForEach-Object {
  [ordered]@{ Class = $_.Class; Name = $_.FriendlyName; InstanceId = $_.InstanceId
    BiosName = (DevProp $_.InstanceId 'DEVPKEY_Device_BiosDeviceName') } })

$r | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 $json
Write-Host "OK. Arquivos gerados:`n  $json"
Write-Host "Revise antes de enviar. Nenhum serial/UUID/MAC foi coletado."
