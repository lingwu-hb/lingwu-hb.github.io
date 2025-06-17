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

REM Update symbolic links
echo.
echo [1/6] Updating post organization...
python update_links.py
if !errorlevel! neq 0 (
    echo Warning: Failed to update post organization.
    echo Continuing with deployment...
)
echo Successfully updated post organization.

REM Git add
echo.
echo [2/6] Adding changes to git...
git add .
if !errorlevel! neq 0 (
    echo Error: Failed to add changes to git.
    echo Please check your git status and try again.
    exit /b 1
)
echo Successfully added changes.

REM Git commit
echo.
echo [3/6] Committing changes...
git commit -m "%commit_msg%"
if !errorlevel! neq 0 (
    echo Error: Failed to commit changes.
    echo Please check your git status and try again.
    exit /b 1
)
echo Successfully committed changes.

REM Git push
echo.
echo [4/6] Pushing to source branch...
git push origin source:source
if !errorlevel! neq 0 (
    echo Error: Failed to push to source branch.
    echo Please check your network connection and try again.
    exit /b 1
)
echo Successfully pushed to source branch.

REM Hexo generate
echo.
echo [5/6] Generating static files...
call hexo g
if !errorlevel! neq 0 (
    echo Error: Failed to generate static files.
    echo Please check your hexo installation and try again.
    exit /b 1
)
echo Successfully generated static files.

REM Hexo deploy
echo.
echo [6/6] Deploying to GitHub Pages...
call hexo d
if !errorlevel! neq 0 (
    echo Error: Failed to deploy to GitHub Pages.
    echo Please check your hexo configuration and try again.
    exit /b 1
)
echo Successfully deployed to GitHub Pages.

echo.
echo Deployment completed successfully! 