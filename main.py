import subprocess
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
import os
import json
from auth import verify_credentials

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("jellyreboot")

app = FastAPI(
    title="JellyReboot",
    description="Jellyfin Container Management API",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def run_command(command: str) -> dict:
    """Execute a command and return both output and error information"""
    try:
        logger.debug(f"Executing command: {command}")
        
        process_info = {
            'user': subprocess.getoutput('whoami'),
            'groups': subprocess.getoutput('groups'),
            'docker_socket_perms': subprocess.getoutput('ls -l /var/run/docker.sock'),
            'docker_group': subprocess.getoutput('getent group docker')
        }
        logger.debug(f"Process info: {json.dumps(process_info, indent=2)}")

        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        output, error = process.communicate()
        
        return {
            'command': command,
            'exit_code': process.returncode,
            'output': output.strip() if output else '',
            'error': error.strip() if error else '',
            'process_info': process_info
        }
    except Exception as e:
        logger.error(f"Command execution failed: {str(e)}")
        return {
            'command': command,
            'exit_code': -1,
            'output': '',
            'error': str(e),
            'process_info': process_info if 'process_info' in locals() else {}
        }

@app.get("/")
async def read_root():
    return FileResponse('static/index.html')

@app.get("/debug")
async def debug_info(username: str = Depends(verify_credentials)):
    try:
        debug_data = {
            'docker_version': run_command('docker --version'),
            'docker_socket': os.path.exists('/var/run/docker.sock'),
            'socket_permissions': run_command('ls -l /var/run/docker.sock'),
            'current_user': run_command('whoami'),
            'user_groups': run_command('groups'),
            'docker_group_info': run_command('getent group docker'),
        }
        return JSONResponse(content=debug_data)
    except Exception as e:
        logger.error(f"Debug info collection failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/status")
async def get_status(username: str = Depends(verify_credentials)):
    try:
        docker_test = run_command('docker ps --format "{{.Names}}"')
        logger.debug(f"Docker test result: {json.dumps(docker_test, indent=2)}")
        
        if docker_test['exit_code'] != 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Docker access failed",
                    "debug_info": docker_test
                }
            )

        ps_result = run_command('docker ps -a --filter "name=jellyfin" --format "{{.Names}} - {{.Status}}"')
        inspect_result = run_command('docker inspect -f "{{.State.Status}}" jellyfin')
        
        return {
            "ps": ps_result['output'],
            "status": inspect_result['output'],
            "debug": {
                "ps_result": ps_result,
                "inspect_result": inspect_result
            }
        }
    except Exception as e:
        logger.exception("Status check failed")
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "debug_info": {
                    "type": str(type(e)),
                    "doc": e.__doc__,
                }
            }
        )

@app.post("/restart")
async def restart_container(username: str = Depends(verify_credentials)):
    try:
        result = run_command('docker restart jellyfin')
        if result['exit_code'] != 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Restart failed",
                    "debug_info": result
                }
            )
        return {"message": "Jellyfin container restarted successfully"}
    except Exception as e:
        logger.exception("Restart failed")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )