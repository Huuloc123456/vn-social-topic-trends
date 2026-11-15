@echo off
setlocal
cd /d "%~dp0.."

set "DOCKER_DESKTOP=%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
if not exist "%DOCKER_DESKTOP%" set "DOCKER_DESKTOP=%LOCALAPPDATA%\Programs\DockerDesktop\Docker Desktop.exe"
if not exist "%DOCKER_DESKTOP%" (
    echo Could not find Docker Desktop. Install it, then run this file again.
    pause
    exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    echo Starting Docker Desktop...
    start "" "%DOCKER_DESKTOP%"
    set "WAIT_COUNT=0"
    goto wait_for_docker
)

goto start_services

:wait_for_docker
timeout /t 5 /nobreak >nul
docker info >nul 2>&1
if not errorlevel 1 goto start_services
set /a WAIT_COUNT+=1
if %WAIT_COUNT% geq 60 goto docker_timeout
goto wait_for_docker

:start_services
echo Starting all Docker Compose services. The first run may take several minutes to build.
docker compose -f "docker\docker-compose.yml" up -d --build
if errorlevel 1 (
    echo Failed to start the project services. See the Docker Compose output above.
    pause
    exit /b 1
)

echo Dashboard: http://127.0.0.1:8501
echo Data appears after the analysis pipeline has written results to MongoDB.
echo Opening all six dashboard pages, HDFS and Spark in the default browser.
start "" "http://127.0.0.1:8501"
start "" "http://127.0.0.1:8501/cau-chuyen"
start "" "http://127.0.0.1:8501/dien-bien"
start "" "http://127.0.0.1:8501/tu-khoa"
start "" "http://127.0.0.1:8501/phan-tich"
start "" "http://127.0.0.1:8501/phuong-phap"
start "" "http://127.0.0.1:9870"
start "" "http://127.0.0.1:9870/explorer.html#/social/youtube_news"
start "" "http://127.0.0.1:8080"
pause
exit /b 0

:docker_timeout
echo Docker Desktop did not become ready within five minutes.
echo Check Docker Desktop, then run this file again.
pause
exit /b 1
