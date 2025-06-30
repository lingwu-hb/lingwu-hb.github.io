@echo off
setlocal enabledelayedexpansion

REM Check if commit message is provided
if "%~1"=="" (
    echo Error: Commit message is required.
    echo Usage: deploy.bat "your commit message"
    exit /b 1
)

REM Store the commit message
set "commit_msg=%~1"

echo Starting deployment process...

REM Check git status
echo.
echo [0/5] Checking for changes...
git status --porcelain > temp_git_status.txt
if !errorlevel! neq 0 (
    echo Error: Failed to check git status.
    echo Please check your git installation and try again.
    del temp_git_status.txt
    exit /b 1
)

REM Check if the temp file is empty (no changes)
for %%F in (temp_git_status.txt) do set size=%%~zF
if !size! equ 0 (
    echo No changes detected in git repository.
    echo Aborting deployment.
    del temp_git_status.txt
    exit /b 0
)
del temp_git_status.txt
echo Changes detected. Proceeding with deployment...

REM Git add
echo.
echo [1/5] Adding changes to git...
git add .
if !errorlevel! neq 0 (
    echo Error: Failed to add changes to git.
    echo Please check your git status and try again.
    exit /b 1
)
echo Successfully added changes.

REM Git commit
echo.
echo [2/5] Committing changes...
git commit -m "%commit_msg%"
if !errorlevel! neq 0 (
    echo Error: Failed to commit changes.
    echo Please check your git status and try again.
    exit /b 1
)
echo Successfully committed changes.

REM Git push
echo.
echo [3/5] Pushing to source branch...
git push origin source:source
if !errorlevel! neq 0 (
    echo Error: Failed to push to source branch.
    echo Please check your network connection and try again.
    exit /b 1
)
echo Successfully pushed to source branch.

REM Hexo generate
echo.
echo [4/5] Generating static files...
call hexo g
if !errorlevel! neq 0 (
    echo Error: Failed to generate static files.
    echo Please check your hexo installation and try again.
    exit /b 1
)
echo Successfully generated static files.

REM Hexo deploy
echo.
echo [5/5] Deploying to GitHub Pages...
call hexo d
if !errorlevel! neq 0 (
    echo Error: Failed to deploy to GitHub Pages.
    echo Please check your hexo configuration and try again.
    exit /b 1
)
echo Successfully deployed to GitHub Pages.

echo.
echo Deployment completed successfully! 