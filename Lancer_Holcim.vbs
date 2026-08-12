Option Explicit

Dim shell, fso, dossierProjet, commande

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Dossier dans lequel se trouve ce fichier .vbs
dossierProjet = fso.GetParentFolderName(WScript.ScriptFullName)

' Lance Streamlit depuis le bon dossier
commande = "cmd /c cd /d """ & dossierProjet & """ && py -m streamlit run app.py --server.headless false"

' 0 = fenêtre complètement cachée
' False = ne pas attendre la fermeture de Streamlit
shell.Run commande, 0, False