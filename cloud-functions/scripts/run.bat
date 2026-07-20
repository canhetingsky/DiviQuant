@echo off
chcp 65001 >nul
title DiviQuant 数据更新

echo ================================================
echo           DiviQuant 数据更新脚本
echo ================================================
echo.

cd /d "%~dp0"

echo [1/2] 开始生成股息数据...
echo --------------------------------
python dividend_data_generator.py

if %errorlevel% neq 0 (
    echo.
    echo ✗ 数据生成失败，退出
    pause
    exit /b %errorlevel%
)

echo.
echo [2/2] 开始上传数据到 S3...
echo --------------------------------
python s3_uploader.py

if %errorlevel% neq 0 (
    echo.
    echo ✗ 上传失败
    pause
    exit /b %errorlevel%
)

echo.
echo ================================================
echo ✓ 数据更新完成！
echo ================================================
echo.

pause