!include "x64.nsh"
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "nsDialogs.nsh"

!define COMPANY_NAME "Mehdi Rajabi"
!define APP_NAME "AudioShelf"
!system 'set /p APP_VER=<VERSION & call echo !define APP_VERSION "%APP_VER%" > version_temp.nsh'
!include "version_temp.nsh"
!delfile "version_temp.nsh"
!define APP_EXE_NAME "audioshelf.exe"
!define SOURCE_DIR "dist\audioshelf"

SetCompressor /SOLID lzma
SetCompressorDictSize 64

Name "${APP_NAME} ${APP_VERSION}"
OutFile "AudioShelf-${APP_VERSION}-Win64-Setup.exe"
InstallDir "$PROGRAMFILES64\${APP_NAME}"
InstallDirRegKey HKLM "Software\${APP_NAME}" "Install_Dir"
RequestExecutionLevel admin

ShowInstDetails hide
ShowUninstDetails hide

Var hRemoveDataCheckbox
Var bRemoveDataState

!define MUI_ABORTWARNING
!define MUI_ICON "AudioShelf.ico" 
!define MUI_UNICON "AudioShelf.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP_NOSTRETCH

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE_NAME}"
!define MUI_FINISHPAGE_RUN_TEXT "Launch ${APP_NAME}"
!define MUI_FINISHPAGE_SHOWREADME
!define MUI_FINISHPAGE_SHOWREADME_TEXT "Create Desktop Shortcut"
!define MUI_FINISHPAGE_SHOWREADME_FUNCTION CreateDesktopShortcut
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
UninstPage custom un.AskRemoveDataPage un.AskRemoveDataPageLeave
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Function .onInit
  ${If} ${RunningX64}
    SetRegView 64
    StrCpy $INSTDIR "$PROGRAMFILES64\${APP_NAME}"
  ${EndIf}
FunctionEnd

Function un.onInit
  ${If} ${RunningX64}
    SetRegView 64
  ${EndIf}
  ReadRegStr $INSTDIR HKLM "Software\${APP_NAME}" "Install_Dir"
FunctionEnd

Function CreateDesktopShortcut
  SetShellVarContext all
  CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE_NAME}"
FunctionEnd

Function un.AskRemoveDataPage
  nsDialogs::Create 1018
  Pop $0
  ${If} $0 == error
    Abort
  ${EndIf}

  GetDlgItem $0 $hwndParent 1
  SendMessage $0 ${WM_SETTEXT} 0 "STR:Uninstall"

  ${NSD_CreateLabel} 0 0 100% 25u "Do you want to delete all your personal data (History, Bookmarks, Settings)?"
  Pop $0

  ${NSD_CreateCheckbox} 0 35u 100% 10u "Yes, delete all my User Data (History, Bookmarks, Settings)"
  Pop $hRemoveDataCheckbox

  SendMessage $hwndParent 0x0028 $hRemoveDataCheckbox 1

  nsDialogs::Show
FunctionEnd

Function un.AskRemoveDataPageLeave
  ${NSD_GetState} $hRemoveDataCheckbox $bRemoveDataState
FunctionEnd

Section "Install" SecInstall
  SetOutPath "$INSTDIR"
  
  RMDir /r "$INSTDIR\_libs"
  RMDir /r "$INSTDIR\_internal"
  RMDir /r "$INSTDIR\lib"
  RMDir /r "$INSTDIR\mpl-data"
  RMDir /r "$INSTDIR\share"
  
  Delete "$INSTDIR\*.dll"
  Delete "$INSTDIR\*.pyd"
  Delete "$INSTDIR\*.so"
  Delete "$INSTDIR\*.exe"
  Delete "$INSTDIR\base_library.zip"
  
  WriteRegStr HKLM "Software\${APP_NAME}" "Install_Dir" "$INSTDIR"
  
  File /r /x ".portable" /x "*.log" /x "user_data" "${SOURCE_DIR}\*.*"
  
  SetShellVarContext all
  CreateDirectory "$SMPROGRAMS\${APP_NAME}"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE_NAME}"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe"

  ${If} ${Silent}
    Call CreateDesktopShortcut
  ${EndIf}

  WriteRegStr HKCR "Directory\shell\AudioShelf" "" "Add to AudioShelf Library"
  WriteRegStr HKCR "Directory\shell\AudioShelf" "Icon" "$INSTDIR\${APP_EXE_NAME}"
  WriteRegStr HKCR "Directory\shell\AudioShelf\command" "" '"$INSTDIR\${APP_EXE_NAME}" "%1"'
  
  WriteRegStr HKCR "*\shell\AudioShelf" "" "Add to AudioShelf Library"
  WriteRegStr HKCR "*\shell\AudioShelf" "Icon" "$INSTDIR\${APP_EXE_NAME}"
  WriteRegStr HKCR "*\shell\AudioShelf\command" "" '"$INSTDIR\${APP_EXE_NAME}" "%1"'

  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayIcon" '"$INSTDIR\${APP_EXE_NAME}"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${COMPANY_NAME}"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoRepair" 1

  WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

Section "Uninstall"
  SetShellVarContext all

  Delete "$SMPROGRAMS\${APP_NAME}\*.*"
  RMDir "$SMPROGRAMS\${APP_NAME}"
  Delete "$DESKTOP\${APP_NAME}.lnk"

  DeleteRegKey HKCR "Directory\shell\AudioShelf"
  DeleteRegKey HKCR "*\shell\AudioShelf"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
  DeleteRegKey HKLM "Software\${APP_NAME}"

  RMDir /r "$INSTDIR\_libs"
  RMDir /r "$INSTDIR\_internal"
  RMDir /r "$INSTDIR\lib"
  RMDir /r "$INSTDIR\mpl-data"
  RMDir /r "$INSTDIR\share"
  RMDir /r "$INSTDIR\tcl"
  
  Delete "$INSTDIR\*.dll"
  Delete "$INSTDIR\*.pyd"
  Delete "$INSTDIR\*.so"
  Delete "$INSTDIR\*.exe"
  Delete "$INSTDIR\*.zip"
  Delete "$INSTDIR\*.dat"
  Delete "$INSTDIR\*.txt"

  ${If} $bRemoveDataState == ${BST_CHECKED}
    SetShellVarContext current
    RMDir /r "$LOCALAPPDATA\${APP_NAME}"
    SetShellVarContext all
    Delete "$INSTDIR\*.log"
    Delete "$INSTDIR\*.json"
  ${EndIf}

  RMDir "$INSTDIR"
SectionEnd