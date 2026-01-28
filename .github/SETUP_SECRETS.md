# GitHub Secrets Setup

This guide explains how to configure secrets for CI/CD pipelines.

## Required Secrets

### 1. CODECOV_TOKEN (Optional but recommended)

For code coverage reporting to Codecov.

**Setup:**
1. Go to [Codecov](https://codecov.io/)
2. Sign in with GitHub
3. Add your repository
4. Copy the upload token
5. Add to GitHub:
   - Go to your repository → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `CODECOV_TOKEN`
   - Value: Paste the token from Codecov

### 2. GITHUB_TOKEN (Automatic)

This is automatically provided by GitHub Actions. No setup required.

**Used for:**
- Docker image push to GitHub Container Registry (ghcr.io)
- Creating releases
- Uploading security scan results

## Optional Secrets (for production deployment)

### 3. AWS Credentials (Future - Phase 9)

For deploying to AWS with Terraform:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`

### 4. Docker Hub Credentials (Alternative to GHCR)

If you want to push to Docker Hub instead of GitHub Container Registry:
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

### 5. Slack/Discord Webhook (Future - Phase 8)

For CI/CD notifications:
- `SLACK_WEBHOOK_URL`
- `DISCORD_WEBHOOK_URL`

## How to Add Secrets

1. **Navigate to repository settings:**
   ```
   Your Repository → Settings → Secrets and variables → Actions
   ```

2. **Click "New repository secret"**

3. **Add the secret:**
   - Name: Secret name (e.g., `CODECOV_TOKEN`)
   - Value: Secret value
   - Click "Add secret"

## Security Best Practices

- ✅ Never commit secrets to the repository
- ✅ Use GitHub Secrets for sensitive data
- ✅ Rotate secrets regularly
- ✅ Use separate secrets for dev/staging/prod
- ✅ Limit secret access to necessary workflows only
- ❌ Never log secrets in workflow output
- ❌ Never use secrets in pull requests from forks

## Verifying Secrets

After adding secrets, you can verify they're working by:

1. **Trigger a workflow run:**
   - Push a commit
   - Or manually trigger via Actions tab

2. **Check workflow logs:**
   - Go to Actions tab
   - Click on the workflow run
   - Check if secrets are being used correctly

**Note:** Secret values are masked in workflow logs for security.

## Troubleshooting

### Codecov upload fails
- Verify `CODECOV_TOKEN` is set correctly
- Check if repository is added to Codecov
- Ensure token has correct permissions

### Docker push fails
- Verify `GITHUB_TOKEN` has package write permissions
- Check if GitHub Packages is enabled for the repository
- Ensure workflow has `packages: write` permission

### Security scan fails
- Trivy scans may take longer for large images
- Check if image was built successfully first
- Verify SARIF upload permissions
