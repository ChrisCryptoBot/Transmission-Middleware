# Git Sync Workflow: Cursor AI Remote Changes

**Purpose:** Sync changes made by Cursor AI on GitHub to your local repository.

---

## Quick Sync Command

```bash
# Fetch all remote changes
git fetch origin

# Check what's different
git log HEAD..origin/master --oneline

# Pull changes (if any)
git pull origin master
```

---

## Detailed Workflow

### 1. Check for Remote Changes

```bash
# Fetch latest from GitHub
git fetch origin

# See what commits are on remote but not local
git log HEAD..origin/master --oneline

# See what commits are local but not remote
git log origin/master..HEAD --oneline
```

### 2. Pull Remote Changes

**If remote is ahead (Cursor AI made changes):**

```bash
# Pull and merge
git pull origin master

# Or if you want to review first
git fetch origin
git log HEAD..origin/master  # Review changes
git merge origin/master      # Merge when ready
```

### 3. Handle Conflicts (if any)

```bash
# If conflicts occur
git status                    # See conflicted files
# Edit files to resolve conflicts
git add <resolved-files>
git commit -m "Merge remote changes from Cursor AI"
```

### 4. Check Other Branches

**If Cursor AI created a feature branch:**

```bash
# List all remote branches
git branch -r

# Check out a remote branch
git checkout -b local-branch-name origin/remote-branch-name

# Or merge a remote branch into master
git merge origin/remote-branch-name
```

---

## Automated Sync Script

Create a script to automate syncing:

```bash
#!/bin/bash
# sync_from_github.sh

echo "Fetching latest changes from GitHub..."
git fetch origin

echo "Checking for remote changes..."
REMOTE_COMMITS=$(git log HEAD..origin/master --oneline | wc -l)

if [ "$REMOTE_COMMITS" -gt 0 ]; then
    echo "Found $REMOTE_COMMITS new commit(s) on remote"
    echo "Recent commits:"
    git log HEAD..origin/master --oneline -5
    
    read -p "Pull changes? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git pull origin master
        echo "✅ Synced successfully!"
    else
        echo "⏸️  Sync cancelled"
    fi
else
    echo "✅ Local is up to date with remote"
fi
```

**Usage:**
```bash
chmod +x sync_from_github.sh
./sync_from_github.sh
```

---

## PowerShell Script (Windows)

```powershell
# sync_from_github.ps1

Write-Host "Fetching latest changes from GitHub..." -ForegroundColor Cyan
git fetch origin

Write-Host "Checking for remote changes..." -ForegroundColor Cyan
$remoteCommits = git log HEAD..origin/master --oneline | Measure-Object -Line

if ($remoteCommits.Lines -gt 0) {
    Write-Host "Found $($remoteCommits.Lines) new commit(s) on remote" -ForegroundColor Yellow
    Write-Host "Recent commits:" -ForegroundColor Yellow
    git log HEAD..origin/master --oneline -5
    
    $response = Read-Host "Pull changes? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        git pull origin master
        Write-Host "✅ Synced successfully!" -ForegroundColor Green
    } else {
        Write-Host "⏸️  Sync cancelled" -ForegroundColor Yellow
    }
} else {
    Write-Host "✅ Local is up to date with remote" -ForegroundColor Green
}
```

**Usage:**
```powershell
.\sync_from_github.ps1
```

---

## Current Status Check

**I can check for you anytime by running:**

```bash
git fetch origin
git status
git log HEAD..origin/master --oneline
```

**Just ask me: "Check for remote changes" or "Sync from GitHub"**

---

## Best Practices

1. **Always fetch first** - See what's changed before pulling
2. **Review changes** - Check what Cursor AI added/modified
3. **Test after merge** - Make sure everything still works
4. **Commit local changes first** - Don't pull with uncommitted work

---

## Troubleshooting

### "Your branch is behind"

```bash
# Pull latest
git pull origin master
```

### "Your branch has diverged"

```bash
# See what's different
git log --oneline --graph --all

# Merge or rebase (your choice)
git pull --rebase origin master  # Rebase (cleaner history)
# OR
git pull origin master           # Merge (preserves history)
```

### "Merge conflicts"

```bash
# See conflicted files
git status

# Resolve conflicts in files
# Then:
git add <resolved-files>
git commit -m "Resolve merge conflicts"
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `git fetch origin` | Download remote changes (doesn't merge) |
| `git pull origin master` | Fetch + merge remote changes |
| `git log HEAD..origin/master` | See remote commits not in local |
| `git log origin/master..HEAD` | See local commits not in remote |
| `git status` | Check current state |
| `git branch -r` | List remote branches |

---

**I can help you sync anytime! Just ask.** 🚀

