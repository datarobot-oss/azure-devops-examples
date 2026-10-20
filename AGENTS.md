# AGENTS.md

Guidance for AI coding agents and for people who start here. This repository holds two Azure DevOps pipelines that deploy an app to DataRobot. The [README](README.md) is the user guide, and each folder under `templates/` has its own README. This file lists what those don't say.

## Help a user adopt an example

1. Pick the example from the release, not from preference. Run `scripts/check_workload_ready.py` with the user's DataRobot endpoint and API key in the environment. It changes nothing. A release with Workloads gets `templates/azure-devops-workload`. A release without them gets `templates/azure-devops-custom-app`.
2. Treat the chosen folder as the root of a new Azure Repos repository. Copy its contents, not the folder, and not the rest of this repository.
3. Replace the sample app with the user's app. The workload example needs a `Dockerfile` at the root of `app/`, a port of 1024 or above, and a `linux/amd64` image.
4. Walk the user through the settings that aren't files. Pipelines can't create them: a variable group named `datarobot-deploy`, an environment named `prod` with an Approval and an Exclusive lock, and a build validation policy on `main`. Each README lists them.
5. For the workload example, the first deploy runs on a person's machine with `dr workload up --yes`, and the user commits `app/.datarobot.yaml`. Without that manifest, every pipeline run creates a new workload.

## Keep these out of the repository

- Never commit a DataRobot API key, an Azure storage key, or a Pulumi passphrase. They live in the `datarobot-deploy` variable group, marked secret.
- Never print or log a token or any secret variable in a pipeline step.
- Don't commit `.datarobot/`, the cache of `dr workload up`. The `.gitignore` excludes it. Do commit `.datarobot.yaml`.
- Use the API key of a service account, not a person.
- Run `uvx pre-commit install` once per clone. The hooks run gitleaks with the rules in `.gitleaks.toml`, which flag a literal value assigned to `DATAROBOT_API_TOKEN`, `AZURE_STORAGE_KEY`, or `PULUMI_CONFIG_PASSPHRASE`. A reference such as `$(DATAROBOT_API_TOKEN)` passes.

## Know how the pipelines behave

- A deploy takes about 8 minutes for the workload example and about 3 minutes for the custom application example. The workload example uploads and rolls a new version on every run, because a CI checkout has no `.datarobot/` cache.
- The first run of a pipeline waits at a **Permit** prompt for the variable group and the `prod` environment. A person approves it in Azure DevOps. A REST token can't do it.
- A pull request prints the plan and never deploys. Only a push to `main` that changes the app reaches the Apply stage and the approval.
- The custom application example keeps its Pulumi state in Azure Blob Storage. A killed run leaves a lock that `pulumi cancel` clears. Check that no run is active first.
- `templates/azure-devops-custom-app/templates/fix-file-times.yml` sets one file time on the app folder so that an unchanged context gives an unchanged plan. Keep it until the `datarobot` provider release that fixes the archive time.
- A top-level `pool:` in an Azure pipeline can't hold template expressions. Put them on each job. A text parameter named after a pool makes the Run pipeline dialog easy to misfill, so name it `selfHostedPool`.

## Check your change

Run the checks in [CONTRIBUTING.md](CONTRIBUTING.md) before you open a pull request: markdownlint, yamllint, and a `docker build` of each sample app you touched. When you change anything under `.github`, CI also audits the workflows with zizmor and actionlint.

When you change a pipeline, run it on Azure DevOps. A YAML edit that passes the linters can still fail on the service. Say in the pull request what you ran, and mark any step you couldn't run as unverified in the README.

## Follow these conventions

- Pin every GitHub Action and container image by full commit SHA or digest, with the version in a comment. Dependabot proposes the updates.
- Pin every tool a pipeline downloads by version, and check its SHA-256, as `azure-devops-workload/templates/install-dr.yml` and `azure-devops-custom-app/templates/install-pulumi.yml` do.
- Keep each `templates/` folder self-contained. A file in one folder must not depend on a file in another.
- Write documentation to the [Google developer documentation style guide](https://developers.google.com/style): sentence-case headings, imperative steps, present tense, and no "we".
- This repository is public. Don't add private DataRobot or customer data.

## Find the details

The following table lists where to look.

| Topic | File |
| --- | --- |
| Choose an example and the shared prerequisites | [README.md](README.md) |
| The workload pipeline, its parameters, and its limits | [templates/azure-devops-workload/README.md](templates/azure-devops-workload/README.md) |
| The custom application pipeline, Pulumi state, and recovery | [templates/azure-devops-custom-app/README.md](templates/azure-devops-custom-app/README.md) |
| A failed or stuck run, with the cause and the fix | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| Whether a DataRobot account supports Workloads | [scripts/check_workload_ready.py](scripts/check_workload_ready.py) |
| Reporting a vulnerability | [SECURITY.md](SECURITY.md) |
