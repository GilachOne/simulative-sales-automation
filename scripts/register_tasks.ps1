$ErrorActionPreference = 'Stop'
$projectDir = Split-Path $PSScriptRoot -Parent
$pythonExe = Join-Path $projectDir '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Сначала создайте .venv' }
$names = @('Simulative_Sales_Generate', 'Simulative_Sales_Load')
foreach ($name in $names) {
    if (Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue) {
        throw "Задача $name уже существует. Проверьте её перед повторной настройкой."
    }
}
$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$options = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 15)
$generateAction = New-ScheduledTaskAction -Execute $pythonExe -Argument ('"' + (Join-Path $projectDir 'generate.py') + '"') -WorkingDirectory $projectDir
$generateTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday,Saturday -At '10:00'
Register-ScheduledTask -TaskName $names[0] -Action $generateAction -Trigger $generateTrigger -Settings $options -Principal $principal -Description 'Кассовые CSV: понедельник — суббота, 10:00' | Out-Null

$loadAction = New-ScheduledTaskAction -Execute $pythonExe -Argument ('"' + (Join-Path $projectDir 'run_load.py') + '"') -WorkingDirectory $projectDir
$loadTrigger = New-ScheduledTaskTrigger -Daily -At '10:15'
Register-ScheduledTask -TaskName $names[1] -Action $loadAction -Trigger $loadTrigger -Settings $options -Principal $principal -Description 'Загрузка CSV в PostgreSQL: ежедневно, 10:15' | Out-Null
Write-Output 'Созданы две задачи. Время используется местное. Нужен вход пользователя в Windows.'
