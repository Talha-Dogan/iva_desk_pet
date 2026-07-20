' Iva kopruyu arka planda (konsol penceresi acmadan) baslatir.
' Kullanim: wscript iva_start_hidden.vbs "C:\...\mcp-bridge" "start_iva_bridge.bat"
Option Explicit

Dim args, targetDir, batName, shell, cmd
Set args = WScript.Arguments

If args.Count >= 1 Then
    targetDir = args(0)
Else
    targetDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & "\..\bridge"
End If

If args.Count >= 2 Then
    batName = args(1)
Else
    batName = "start_iva_bridge.bat"
End If

Set shell = CreateObject("WScript.Shell")
shell.CurrentDirectory = targetDir
cmd = "cmd /c """ & targetDir & "\" & batName & """"
' 0 = gizli pencere, False = bitmesini bekleme
shell.Run cmd, 0, False
