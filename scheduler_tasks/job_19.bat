@echo off
REM Scheduled Task Batch File for Job 19
REM Module: new1 (ID: 4)
REM Created: 2025-11-23 20:06:17

echo ================================================================================
echo SCHEDULED TASK EXECUTION - Job 19
echo Module: new1
echo Time: %date% %time%
echo ================================================================================

cd /d "C:\Users\Devesh\practise files\testingapp\Testing-Automation"
"C:\Users\Devesh\AppData\Local\Programs\Python\Python39\python.exe" "C:\Users\Devesh\practise files\testingapp\Testing-Automation\execute.py" --module-id 4 --module-name "new1" --browser Chrome --headless false

echo.
echo ================================================================================
echo Execution completed
echo ================================================================================
