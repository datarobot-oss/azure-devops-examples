# Troubleshooting

Fixes for common failures of the two example pipelines. Each fix names the cause, so a similar failure in an adapted pipeline is quicker to place. For failures that belong to one example, see the "Recover from a failure" and "Limits" sections of its README.

## Both examples

The following table lists failures that apply to both pipelines.

| Symptom | Cause | Fix |
| --- | --- | --- |
| The first run waits and no job starts. | A pipeline needs permission to use a variable group and an environment on its first run. | Open the run and select **Permit** for each resource. A person has to do this in Azure DevOps. |
| The run fails with `Could not find a pool with name prod`. | The `selfHostedPool` parameter holds the environment name. The **Run pipeline** dialog makes this easy to misfill. | Clear the parameter to use a Microsoft-hosted agent, or enter the name of a self-hosted pool. |
| A pull request prints no plan. | The pipelines set `pr: none`. The plan comes from a build validation policy on `main`, which starts when the pull request is opened. A push to the branch doesn't start it. | Add the build validation policy (step 5 of the setup in each README), then open the pull request. |
| A push to `main` is rejected. | The build validation policy requires a pull request. | Open a pull request. |
| A merge to `main` starts no deploy. | The pipeline triggers only on a change under the app folders. The Apply stage runs only on `main`. | Change a file under the paths in the `trigger` block, or run the pipeline on `main` by hand. |
| The run waits at the approval and nobody can approve it. | `requesterCannotBeApprover` is on, so the person who started the run can't approve it. | Add a second approver to the Approval check on the `prod` environment. |
| A step can't read a secret variable. | Azure DevOps doesn't pass secret variables to scripts on its own. | Map each secret in the `env:` block of the step, as the pipelines do, for example `DATAROBOT_API_TOKEN: $(DATAROBOT_API_TOKEN)`. |
| The YAML is rejected for a template expression in a top-level `pool:`. | A top-level `pool:` can't hold template expressions. | Put the `pool:` block on each job, as the pipelines do. |
| A step times out against the DataRobot endpoint. | A Microsoft-hosted agent reaches multi-tenant SaaS, but it can't reach an environment that isn't open to the public internet. | Use a self-hosted pool with a route to the endpoint. Unverified: no self-hosted agent was tested. |
| The smoke test prints HTTP 401 or 503 on the first attempts. | A new route can answer 401 or 503 for about 20 seconds. | None. The step retries six times, 10 seconds apart. If all six fail, read the deploy log. |

## Workload example

The following table lists failures that apply to `azure-devops-workload`.

| Symptom | Cause | Fix |
| --- | --- | --- |
| Every run creates a new workload, or the plan says the workload "will be created". | The manifest with the `workloadId` isn't committed. `dr workload up` doesn't adopt a workload by name. | Deploy once from a workstation, then commit `app/.datarobot.yaml`. See step 1 of the setup. |
| `dr workload up` fails with HTTP 422. | Two runs deployed at the same time. | Add an Exclusive lock check to the `prod` environment, then run the pipeline again. |
| A deploy takes about 8 minutes with no code change. | A CI checkout has no `.datarobot/` cache, so each run uploads the code and rolls a new version. | None. The path filters keep unrelated commits from starting a deploy. |
| `scripts/check_workload_ready.py` reports `ENABLE_WORKLOAD_API_ARTIFACTS_AND_WORKLOADS` as off, and the deploy works. | That flag doesn't gate workloads. | Ignore it. The script shows it for information only. |

## Custom Application example

The following table lists failures that apply to `azure-devops-custom-app`. The README of the example covers the stale Pulumi lock, the orphaned application that blocks `pulumi destroy`, and the plugin download that answers 403.

| Symptom | Cause | Fix |
| --- | --- | --- |
| Each run plans a rebuild of the environment. | The zip of the Docker context carries file times, and a checkout writes new times. | Keep the `fix-file-times.yml` step in both stages. |
| `CustomApplicationFromEnvironment` fails on create with `Struct defines fields not found in object`. | A defect in the `datarobot` provider 0.10.43 and 0.10.45. | Use `ExecutionEnvironment`, `ApplicationSource`, and `CustomApplication`, as `Pulumi.yaml` does. |
| The apply fails with 409 on the source. | DataRobot rejects two sources with the same name, so the new source has to exist before the old one goes. | Keep the environment version in the source name, as `Pulumi.yaml` does. |
