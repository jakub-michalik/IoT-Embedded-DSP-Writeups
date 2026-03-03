@ECHO OFF
pushd %~dp0

if "%1" == "" goto help
if "%1" == "help" goto help
if "%1" == "html" goto html
if "%1" == "clean" goto clean

goto help

:help
echo Usage: make ^<target^>
echo.
echo Targets:
echo   html     Build HTML documentation
echo   clean    Remove build artifacts
goto end

:html
sphinx-build -b html -c . .. _build\html %SPHINXOPTS%
echo Build finished. Output in _build\html\
goto end

:clean
if exist _build rmdir /s /q _build
goto end

:end
popd
