@echo off
chcp 65001 >nul
setlocal

set "HERE=%~dp0"
set "PY="

where py >nul 2>nul && set "PY=py -3"
if not defined PY ( where python >nul 2>nul && set "PY=python" )
if not defined PY (
  if exist "C:\Users\%USERNAME%\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" (
    set "PY=C:\Users\%USERNAME%\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
  )
)
if not defined PY (
  echo 没找到 Python。请先安装 Python 3，或把 python.exe 所在目录加入 PATH。
  pause
  exit /b 1
)

echo 使用解释器: %PY%
echo.
%PY% "%HERE%armor.py" install %*
echo.
pause
