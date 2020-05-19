Set oShell = CreateObject ("Wscript.Shell") 
Dim strArgs
strArgs = "cmd /c run_bike_checker.bat"
oShell.Run strArgs, 0, false