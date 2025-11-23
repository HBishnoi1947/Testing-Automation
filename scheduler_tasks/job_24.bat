@echo off
REM Scheduled Task Batch File for Job 24
REM Module: new1 (ID: 4)
REM Created: 2025-11-23 22:16:26

echo ================================================================================ > "C:\Users\Devesh\practise files\testingapp\Testing-Automation\scheduler_tasks\job_24_log.txt"
echo SCHEDULED TASK EXECUTION - Job 24 >> "C:\Users\Devesh\practise files\testingapp\Testing-Automation\scheduler_tasks\job_24_log.txt"
echo Module: new1 >> "C:\Users\Devesh\practise files\testingapp\Testing-Automation\scheduler_tasks\job_24_log.txt"
echo Start Time: %date% %time% >> "C:\Users\Devesh\practise files\testingapp\Testing-Automation\scheduler_tasks\job_24_log.txt"
echo ================================================================================ >> "C:\Users\Devesh\practise files\testingapp\Testing-Automation\scheduler_tasks\job_24_log.txt"
echo. >> "C:\Users\Devesh\practise files\testingapp\Testing-Automation\scheduler_tasks\job_24_log.txt"

cd /d "C:\Users\Devesh\practise files\testingapp\Testing-Automation"
echo Working Directory: %CD% >> "C:\Users\Devesh\practise files\testingapp\Testing-Automation\scheduler_tasks\job_24_log.txt"
echo. >> "C:\Users\Devesh\practise files\testingapp\Testing-Automation\scheduler_tasks\job_24_log.txt"

echo Executing Python Script... >> "C:\Users\Devesh\practise files\testingapp\Testing-Automation\scheduler_tasks\job_24_log.txt"
"C:\Users\Devesh\AppData\Local\Programs\Python\Python39\python.exe" "C:\Users\Devesh\practise files\testingapp\Testing-Automation\execute.py" --module-id 4 --module-name "new1" --browser Chrome --headless false >> "C:\Users\Devesh\practise files\testingapp\Testing-Automation\scheduler_tasks\job_24_log.txt" 2>&1

echo. >> "C:\Users\Devesh\practise files\testingapp\Testing-Automation\scheduler_tasks\job_24_log.txt"
echo ================================================================================ >> "C:\Users\Devesh\practise files\testingapp\Testing-Automation\scheduler_tasks\job_24_log.txt"
echo End Time: %date% %time% >> "C:\Users\Devesh\practise files\testingapp\Testing-Automation\scheduler_tasks\job_24_log.txt"
echo Exit Code: %ERRORLEVEL% >> "C:\Users\Devesh\practise files\testingapp\Testing-Automation\scheduler_tasks\job_24_log.txt"
echo ================================================================================ >> "C:\Users\Devesh\practise files\testingapp\Testing-Automation\scheduler_tasks\job_24_log.txt"

REM Keep window open for 5 seconds to see output
timeout /t 5 /nobreak > nul
