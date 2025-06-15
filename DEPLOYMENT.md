# Automatic Deployment Setup

This repository is configured for automatic deployment to your VPS whenever you push code to the `main` or `master` branch.

## GitHub Secrets Setup

You need to add these secrets to your GitHub repository:

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add each of these:

### Required Secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `VPS_HOST` | `5.250.177.235` | Your VPS IP address |
| `VPS_USER` | `root` | SSH username for your VPS |
| `VPS_SSH_KEY` | See below | Private SSH key for authentication |
| `TELEGRAM_BOT_TOKEN` | `YOUR_TELEGRAM_BOT_TOKEN` | Your Telegram bot token |
| `ANTHROPIC_API_KEY` | `YOUR_ANTHROPIC_API_KEY` | Your Anthropic API key |

### SSH Private Key (`VPS_SSH_KEY`):
Copy the private key that was generated during setup. You can find it in your deployment setup output or generate a new one with:
```bash
ssh-keygen -t rsa -b 4096 -C "github-actions-deploy"
```
Then add the public key to your VPS's `~/.ssh/authorized_keys` file.

## How It Works

1. **Trigger**: Deployment runs automatically when you push to `main` or `master` branch
2. **Process**: 
   - Copies your code to the VPS
   - Updates environment variables
   - Rebuilds and restarts the Docker container
   - Verifies the deployment was successful
3. **Manual Trigger**: You can also trigger deployment manually from GitHub Actions tab

## Monitoring Deployments

- Go to your GitHub repository → **Actions** tab to view deployment status
- Click on any workflow run to see detailed logs
- Failed deployments will show error details

## Manual Deployment

If you need to deploy manually:
```bash
./deploy.sh 5.250.177.235 root
```

## Troubleshooting

If deployment fails:
1. Check the GitHub Actions logs
2. Verify all secrets are correctly set
3. SSH to your VPS and check: `docker compose logs -f`
4. Restart manually: `systemctl restart telegram-teacher-bot`