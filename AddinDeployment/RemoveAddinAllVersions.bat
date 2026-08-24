@echo off

pushd %~dp0

for %%i in (2022 2023 2024 2025 2026) do (
	echo.
	echo Removing BatchRvt addin for Revit %%i
	call RemoveAddin.bat %%i
	)

echo Done.
echo.

popd
