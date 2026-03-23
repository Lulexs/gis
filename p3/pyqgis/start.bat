@echo off
setlocal

set "QGISROOT=C:\Program Files\QGIS 3.40.15"

set "QGIS_PREFIX_PATH=%QGISROOT%\apps\qgis-ltr"
set "QT_PLUGIN_PATH=%QGISROOT%\apps\Qt5\plugins"
set "PATH=%QGISROOT%\bin;%QGISROOT%\apps\qgis-ltr\bin;%QGISROOT%\apps\Qt5\bin;%QGISROOT%\apps\Python312;%QGISROOT%\apps\Python312\Scripts;%PATH%"

set "PYTHONHOME=%QGISROOT%\apps\Python312"
set "PYTHONPATH=%QGISROOT%\apps\qgis-ltr\python;%QGISROOT%\apps\Python312\Lib\site-packages"

"%QGISROOT%\bin\python.exe" "%~dp0main.py"

endlocal