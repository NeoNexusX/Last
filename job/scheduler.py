"""Task scheduling module for managing background tasks and periodic jobs."""

from apscheduler.schedulers.background import BackgroundScheduler
from job.cmds_pool import get_cmds_all
from logger import get_logger
from job.task_pool import get_tasks_all
from ssh.ssh_manager import execute_commands, get_ssh_connection

logger = get_logger("main.task_scheduler")

SCHEDULER = BackgroundScheduler()


async def cmd_handler(cmd_name, ip, port, username, password):
    """Execute a command on a remote server via SSH
    
    Args:
        cmd_name: Name of the command to execute from cmds.yaml
        ip: Server IP address
        port: SSH port number
        username: SSH username
        password: SSH password
        
    Returns:
        Dict[str, Result]: Dictionary of Result objects with command execution results
        
    Raises:
        Exception: If command execution fails
    """
    try:
        # Get command set and refresh to ensure latest commands
        cmd_sets = get_cmds_all()
        cmd_sets.refresh()
        
        # Get specific command configuration
        cmds = cmd_sets.get_cmds()[cmd_name]
        
        # Establish SSH connection
        connection = await get_ssh_connection(ip, username, password, port)
        if not connection:
            logger.error(f"Failed to establish SSH connection to {ip}:{port}")
            return {}
            
        # Execute commands and return results
        logger.info(f"Executing command set '{cmd_name}' on {ip}:{port}")
        results = await execute_commands(connection, cmds.cmds)
        return results
        
    except KeyError:
        logger.error(f"Command '{cmd_name}' not found in command definitions")
        return {}
    except Exception as e:
        logger.error(f"Error executing command '{cmd_name}': {str(e)}")
        return {}


async def task_handler(task_name, ip, port, username, password):
    """Handle task execution by running a sequence of commands
    
    Args:
        task_name: Name of the task to execute from tasks.yaml
        ip: Server IP address
        port: SSH port number
        username: SSH username 
        password: SSH password
        
    Returns:
        None
    """
    logger.info(f"Task '{task_name}' started on {ip}:{port}")
    
    try:
        # Get task configuration
        task = get_tasks_all().get_task()[task_name]
        
        # Execute each command in the task
        for cmd in task.cmds:
            logger.info(f"Executing command '{cmd.name}' as part of task '{task_name}'")
            results = await cmd_handler(cmd.name, ip, port, username, password)
            await results_handler(results)
            
        logger.info(f"Task '{task_name}' completed successfully")
        
    except KeyError:
        logger.error(f"Task '{task_name}' not found in task definitions")
    except Exception as e:
        logger.error(f"Error executing task '{task_name}': {str(e)}")


async def results_handler(results):
    """Process command execution results, output stdout and stderr, and log results
    
    Args:
        results: Result dictionary returned by execute_commands, keys are command names, values are Result objects
    """
    for cmd_name, result in results.items():
        if result.ok:
            logger.info(f"Command '{cmd_name}' executed successfully")
            logger.info(f"Output: {result.stdout.strip()}")
        else:
            logger.error(f"Command '{cmd_name}' failed with exit code: {result.exited}")
            logger.error(f"Error message: {result.stderr.strip()}")
            
        # Detailed logging
        logger.debug(f"Command details - '{cmd_name}':")
        logger.debug(f"  Original command: {result.command}")
        logger.debug(f"  Exit code: {result.exited}")
        logger.debug(f"  stdout: {result.stdout}")
        logger.debug(f"  stderr: {result.stderr}")

def task_cmds_update(cmds_name,task):
    task.task.cmds[cmds_name]
# TODO：定时任务触发
