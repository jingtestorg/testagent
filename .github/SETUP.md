# GitHub Setup for Joule Studio

## Overview

Production deployment in Joule Studio uses GitHub as the promotion mechanism. A developer pushes their solution to a GitHub repository, and an administrator manually triggers a GitHub Action to deploy it to the productive environment. This manual trigger is the deliberate approval gate for production.

Authentication between GitHub Actions and SAP Cloud Identity Services (SCI) uses OAuth 2.0 client credentials. The workflow exchanges an SCI client ID and client secret for a short-lived access token, which it then uses to call the Joule Studio solution management API.

> **Note:** You only need GitHub setup once you're ready to promote a solution to production. It's not a prerequisite for building, testing, or running solutions in the development environment. Development deployments can be done directly from Joule Studio. See [Deployment](https://help.sap.com/docs/business-ai-platform/joule-studio/deployment).

---

## Prerequisites

- Core Components, Joule, and Joule Studio are provisioned for both environments. See [Provisioning](https://help.sap.com/docs/business-ai-platform/joule-studio/provisioning).
- Your organization has a GitHub license (GitHub.com or an enterprise license). The GitHub instance must be internet-accessible and not behind a VPN.
- You have administrator access to your SCI tenant.
- You are a GitHub organization owner, or an organization owner can configure Actions variables and secrets for you.

---

## Step 1: Configure Client Credentials in SAP Cloud Identity Services

### Create an Application in IAS

1. Log in to the SCI administration console at `https://<your-sci-tenant>.accounts.ondemand.com/admin`.

2. Go to **Applications & Resources** and select the **Applications** tile.

3. Select **Create** and fill in the dialog:
   - **Display Name:** Use a name that identifies your GitHub organization, for example `github.com/<your-org>`.
   - **Type:** Non-SAP solution
   - **Parent application:** None
   - **Organization ID:** global
   - **Protocol Type:** OpenID Connect

4. Select **Create** and open the newly created application.

> **Note:** OpenID Connect is the SCI application protocol used to expose the OAuth token endpoint. Selecting it does not enable GitHub OIDC federation; the workflow in this repository authenticates with a client ID and client secret.

### Create a Client Secret

1. On the **Trust** tab, under **Application APIs**, select **Client Authentication**.

2. Note the displayed **Client ID**. You will store it as the `SCI_CLIENT_ID` GitHub organization variable in Step 3.

3. Under **Secrets**, select **Add** and create a client secret according to your organization's expiration policy.

4. Copy the secret when it is displayed. You will store it as the `SCI_CLIENT_SECRET` GitHub organization secret in Step 3.

> **Important:** Treat the client secret as a password. Do not commit it to the repository, paste it into the workflow file, or expose it in workflow logs. Rotate it immediately if it is disclosed.

### Define a Dependency to the Joule Studio Application

1. Still on the **Trust** tab, under **Application APIs**, select **Dependencies**.

2. Select **Add** and fill in the dialog:
   - **Dependency Name:** `build`
   - **Application:** Select `Build Core SAP Managed IAS (engagement layer)`
   - **API:** Select `solution-deployment`

3. Select **Save**.

---

## Step 2: Create a GitHub Repository and Connect Your Solution

### Create a GitHub Repository

1. Log in to GitHub and select **New repository**.
2. Set the owner to your GitHub organization.
3. Enter a repository name that identifies the solution.
4. Set **Visibility** to **Private**.
5. Leave all other options at their defaults (no template, no README, no `.gitignore`, no license).
6. Select **Create repository**.

### Connect Your Solution to GitHub

Connect your solution from Joule Studio to the repository you just created:

1. Open your solution in Joule Studio.
2. Open the **More options** menu (⋯).
3. Choose **Connect to GitHub**.
4. Enter your GitHub repository URL.

   > **Note:** If you are using GitHub Enterprise, make sure your administrator has completed the GitHub Enterprise setup first.

5. Choose **Connect to GitHub** and authenticate.

Once connected, the repository is associated with your solution. You cannot change the connected repository later.

Push changes to GitHub directly from Joule Studio using **Push to GitHub**. This will also push the workflow file to the repository:

```text
.github/workflows/deploy.yml
```

> **Note:** The workflow file is pushed only if it does not already exist in the repository. Joule Studio will never overwrite it, so you are free to customize it to fit your needs. If you delete the file and push again from Joule Studio, it will be restored to the default template.

> **Reference:** A reference copy of the workflow configuration is maintained in an external repository:
> `https://github.com/SAP-samples/lifecycle-operations-for-joule-studio`

---

## Step 3: Configure GitHub Organization Variables and Secret

Use organization-level configuration to share the SCI credentials and landscape URLs without duplicating them in every repository. Restrict each variable and secret to the repositories that are allowed to deploy.

### Configure Organization Variables

1. In GitHub, open your organization.
2. Go to **Settings > Secrets and variables > Actions > Variables**.
3. Create the following variables:

| Variable | Description |
|---|---|
| `SCI_TENANT_URL` | Issuer URI of your SCI tenant, for example `https://<your-tenant>.accounts.ondemand.com` |
| `SCI_CLIENT_ID` | Client ID from the SCI application created in Step 1 |
| `SOLUTION_HANDLING_API_BASE_URL` | Base URL of the Joule Studio solution management API for your landscape |

4. For each variable, set **Repository access** to **Selected repositories** and select only the repositories that are allowed to deploy.

### Configure the Organization Secret

1. Go to **Settings > Secrets and variables > Actions > Secrets**.
2. Select **New organization secret**.
3. Set the name to `SCI_CLIENT_SECRET` and enter the client secret created in Step 1.
4. Set **Repository access** to **Selected repositories** and select only the repositories that are allowed to deploy.

The workflow reads the configuration through the following GitHub contexts:

```yaml
sciTenantUrl: ${{ vars.SCI_TENANT_URL }}
sciClientId: ${{ vars.SCI_CLIENT_ID }}
sciClientSecret: ${{ secrets.SCI_CLIENT_SECRET }}
jouleStudioUrl: ${{ vars.SOLUTION_HANDLING_API_BASE_URL }}
```

> **Important:** Repository access controls which repositories can read an organization variable or secret. It does not restrict the value to a particular workflow within an allowed repository. Protect changes to `.github/workflows/` and `.github/actions/`, and require review from trusted maintainers.

> **GitHub Free:** Organization-level Actions secrets and variables are not available to private repositories on GitHub Free. Use a GitHub plan that supports this configuration for private repositories. Do not make solution source code public solely to work around this restriction.

---

## Step 4: Run the Workflow

1. In your GitHub repository, go to **Actions**.
2. Select **Deploy to Joule Studio**.
3. Select **Run workflow**.
4. Choose the branch or tag to deploy.
5. Select **Run workflow** to start the deployment.

The workflow performs the following operations:

1. Checks out the selected branch or tag.
2. Installs the Joule Studio CLI.
3. Exchanges the SCI client ID and client secret for a short-lived SCI access token.
4. Builds the solution archive.
5. Deploys the archive to Joule Studio.

### Workflow Structure

The workflow is defined as a manually triggered workflow (`workflow_dispatch`) with a single **Deploy to Joule Studio** job, which performs the following operations in order:

| Phase | What it does |
|---|---|
| Checkout | Checks out the selected branch or tag |
| Setup CLI | Installs Node.js and the Joule Studio CLI |
| Obtain SCI token | Exchanges the SCI client ID and client secret for a short-lived access token |
| Build | Runs `jl solution build` to create the solution archive |
| Deploy | Runs `jl solution deploy <archive> --force` to deploy the solution |

> **Security Note:** The client secret is read only from the GitHub `secrets` context. The workflow masks the short-lived SCI token and does not print the secret or token response.

Once the workflow completes, the agent is live in the productive environment. Deployment status is visible directly in GitHub Actions.

Administrators can also view the solution, its deployments, and observability data in the Joule Studio productive environment.

---

## Step 5: Test the Basic Setup Flow

Use a dedicated test solution and repository before enabling production repositories.

1. Confirm that the repository is selected for all three organization variables and the `SCI_CLIENT_SECRET` organization secret.
2. Push the solution and `.github/workflows/deploy.yml` to the repository's default branch.
3. In **Actions**, select **Deploy to Joule Studio** and run the workflow from the default branch.
4. Confirm that checkout, CLI setup, token retrieval, build, and deploy all succeed.
5. In Joule Studio, confirm that the deployed solution name and version match `solution.yaml` and that the expected assets are available.
6. Review the workflow log and confirm that it does not contain the client secret or a complete SCI access token.

The basic setup test is successful when the selected repository can deploy the intended solution and no credentials are exposed.

---

## Step 6: Test Deployment from a Tag

Use the branch and tag selector in the **Run workflow** dialog to deploy a tagged solution version. Before running the workflow, verify that:

- The tag points to the intended commit.
- The version in `solution.yaml` matches the version represented by the tag.
- The `.build` file identifies the intended Joule Studio solution.
- All files referenced by `solution.yaml`, including asset descriptors and source files, exist at that tag.

To run the test:

1. Create a version tag for the intended commit, for example `1.1.0`.
2. In **Actions**, select **Deploy to Joule Studio** and then select **Run workflow**.
3. Open the ref selector, choose **Tags**, and select the version tag.
4. Run the workflow.
5. Confirm in the checkout log that the workflow used the commit referenced by the tag.
6. Confirm in Joule Studio that the expected solution version and content were deployed.

If your release process permits moving an existing tag, test the re-tag behavior explicitly. Confirm that the workflow checks out the new commit and that the resulting deployment either updates the existing version as designed or fails with the expected immutable-version error.

---

## Step 7: Test the Download Flow

Use this flow to verify that a solution downloaded from Joule Studio can be stored in GitHub and deployed by the reference workflow.

1. In Joule Studio, locate the test solution and the version that you want to download.
2. Open the solution's **More options** menu (⋯) and select **Download ZIP**.
3. Wait for the **Preparing Download** dialog to complete. The ZIP download starts automatically.
4. Extract the ZIP into a temporary local directory.
5. Verify the downloaded content:
   - `solution.yaml` is present and contains the expected solution name and version.
   - `.build` is present and identifies the intended solution.
   - Every file referenced by `solution.yaml` is present under `assets/`.
   - Intent and requirement files expected for the solution are present.
   - No credentials, access tokens, or local temporary files are included.
6. Copy the extracted solution content to the root of the GitHub repository. Do not add an extra parent directory around the solution files.
7. If the ZIP does not contain the GitHub workflow and actions, add the reference files under `.github/`, using the standard workflow name `.github/workflows/deploy.yml`.
8. Commit and push the files, then run **Deploy to Joule Studio** from the corresponding branch or tag.
9. Confirm that the downloaded solution builds and deploys successfully and that the deployed content matches the source version in Joule Studio.

---

## Step 8: Verify Repository Access

Verify the **Selected repositories** policy before using the configuration for production deployment:

1. Run the workflow from a selected repository and confirm that the client credentials exchange succeeds.
2. Run a configuration check from a repository that is not selected, or temporarily remove a test repository from the access list.
3. Confirm that `SCI_CLIENT_SECRET` is unavailable and that the workflow fails before it calls the SCI token endpoint.
4. Restore the selected repository access after the test.

Do not print the secret to determine whether it is available. A check should report only whether the value is set.

---

## Optional Extension: OIDC Federation

GitHub Actions can also authenticate to SCI by exchanging a GitHub-issued OpenID Connect token instead of storing a long-lived client secret. This can reduce secret rotation and storage requirements.

OIDC federation is not implemented by the workflow and actions in this repository. Implementing it requires additional configuration, including:

- Granting the workflow `id-token: write` permission.
- Configuring the GitHub token issuer and JSON Web Key Set URI in SCI.
- Restricting trusted subject claims to the intended organization, repository, branch, tag, or deployment environment.
- Replacing the client-secret exchange in the token-fetch action with a GitHub OIDC token exchange.

Branch and tag workflow runs can produce different subject claims. If you implement this extension, define and test the trust policy for every supported ref type before using it for production deployment.

---

## Additional Resources

- [GitHub Actions documentation](https://docs.github.com/actions)
- [Using secrets in GitHub Actions](https://docs.github.com/actions/security-guides/using-secrets-in-github-actions)
- [Using variables in GitHub Actions](https://docs.github.com/actions/learn-github-actions/variables)
- [SAP Cloud Identity Services documentation](https://help.sap.com/docs/identity-authentication)
- [Joule Studio Deployment Guide](https://help.sap.com/docs/business-ai-platform/joule-studio/deployment)

---

**Last Updated:** 2026-09-07
