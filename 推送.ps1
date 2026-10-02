#Requires -Version 5.1
<#
.SYNOPSIS
  把破甲指令包按原有目录结构推送到 GitHub 仓库。

.DESCRIPTION
  GitHub MCP 若配置的是只读 PAT（建仓 / 写文件会 403），用本脚本走 git 直接推送。
  脚本在临时目录里建立仓库，不污染包目录；推送完成后自动清理。

.EXAMPLE
  # 用环境变量里的 token 推送
  $env:GITHUB_TOKEN = 'ghp_xxx'
  .\推送.ps1 -Repo 0518a/workbuddy-pojia-aaa

.EXAMPLE
  # 只做本地演练（初始化 + 提交，不联网推送）
  .\推送.ps1 -Repo 0518a/workbuddy-pojia-aaa -DryRun

.EXAMPLE
  # 临时传 token（会留在命令历史里，不如用环境变量）
  .\推送.ps1 -Repo 0518a/workbuddy-pojia-aaa -Token ghp_xxx
#>
param(
    [Parameter(Mandatory = $true)][string]$Repo,          # owner/repo
    [string]$Token  = $env:GITHUB_TOKEN,
    [string]$Branch = 'main',
    [string]$Source = '',
    [string]$Message = 'feat: 初始化 WorkBuddy 破甲指令包（完整结构，18 个文件）',
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($Source)) {
    if ($PSScriptRoot) { $Source = $PSScriptRoot }
    elseif ($MyInvocation.MyCommand.Path) { $Source = Split-Path -Parent $MyInvocation.MyCommand.Path }
    else { $Source = (Get-Location).Path }
}

if ($Repo -notmatch '^[^/]+/[^/]+$') { throw "Repo 参数必须是 owner/repo 形式，当前：$Repo" }
$owner, $name = $Repo -split '/', 2

if (-not $DryRun -and [string]::IsNullOrWhiteSpace($Token)) {
    throw "缺少 token。请设置 `$env:GITHUB_TOKEN='ghp_xxx'（需要 Contents: Read and write，或 classic token 的 repo scope），或加 -DryRun 只做本地演练。"
}

if (-not (Test-Path (Join-Path $Source 'armor.py'))) {
    throw "源目录里找不到 armor.py，Source 指向的不是指令包目录：$Source"
}

$work = Join-Path ([System.IO.Path]::GetTempPath()) ("wb-armor-push-" + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $work -Force | Out-Null

try {
    # 1. 复制全部文件，保持目录层级（排除 VCS / 缓存）
    Get-ChildItem -Path $Source -Force | Where-Object {
        $_.Name -notin @('.git', '__pycache__', '.armor-backup')
    } | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $work -Recurse -Force
    }
    Get-ChildItem -Path $work -Recurse -Force -Directory |
        Where-Object { $_.Name -eq '__pycache__' } |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    $files = Get-ChildItem -Path $work -Recurse -Force -File |
             ForEach-Object { $_.FullName.Substring($work.Length + 1) } | Sort-Object
    Write-Host ("[1/5] 待推送文件 {0} 个：" -f $files.Count) -ForegroundColor Cyan
    $files | ForEach-Object { Write-Host "      $_" }

    # 2. 初始化仓库
    git -C $work init -q -b $Branch
    git -C $work config user.name  ($owner)
    git -C $work config user.email "$owner@users.noreply.github.com"
    git -C $work config core.autocrlf false
    git -C $work config core.quotepath false
    Write-Host "[2/5] 本地仓库已初始化（分支 $Branch，autocrlf=false 保持字节一致）" -ForegroundColor Cyan

    # 3. 提交
    git -C $work add -A
    git -C $work commit -q -m $Message
    $sha = (git -C $work rev-parse HEAD).Trim()
    Write-Host "[3/5] 已提交 $sha" -ForegroundColor Cyan

    if ($DryRun) {
        Write-Host "[4/5] -DryRun：跳过远端推送" -ForegroundColor Yellow
        Write-Host ("[5/5] 演练完成。共 {0} 个文件已可提交；这次没有用到的 token。" -f $files.Count) -ForegroundColor Green
        return
    }

    # 4. 推送（token 只进 remote URL，不打印）
    $remote = "https://x-access-token:$Token@github.com/$owner/$name.git"
    git -C $work remote add origin $remote
    Write-Host "[4/5] 推送到 github.com/$Repo …" -ForegroundColor Cyan
    git -C $work push -u origin $Branch --quiet
    if ($LASTEXITCODE -ne 0) { throw "推送失败（exit $LASTEXITCODE）" }

    # 5. 收尾
    git -C $work remote set-url origin "https://github.com/$Repo.git"
    Write-Host ("[5/5] 完成。{0} 个文件已推送到 https://github.com/{1}/tree/{2}" -f $files.Count, $Repo, $Branch) -ForegroundColor Green
}
finally {
    if (Test-Path $work) { Remove-Item -Path $work -Recurse -Force -ErrorAction SilentlyContinue }
}
