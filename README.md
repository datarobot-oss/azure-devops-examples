# DataRobot deploy examples for Azure DevOps

Two pipelines that deploy an app to DataRobot from Azure DevOps. A pull request prints the plan. A merge to `main` waits for an approval, deploys, and runs a smoke test.

The following table lists the two examples.

| Folder | Deploys | Use it when |
| --- | --- | --- |
| `templates/azure-devops-workload` | A container as a DataRobot Workload, with `dr workload up`. | The DataRobot release has Workloads. |
| `templates/azure-devops-custom-app` | A container as a Custom Application, with Pulumi and the state in Azure Blob Storage. | The release has no Workloads, or Custom Applications already run. |

Treat each folder as the root of its own repository. Copy its contents into an Azure Repos repository, then follow its `README.md`. Both examples include a small Spring Boot sample, and the workload example also has a Python sample. Replace the sample with the app to deploy.

## Before you start

Complete these steps before the first run.

1. Check which example fits the release. `scripts/check_workload_ready.py` reads what the DataRobot account allows. It needs `uv` or Python 3 (3.12 is the tested version), plus the DataRobot endpoint and an API key in the environment. It changes nothing.
2. Use the key of a service account, not a person, and store it as a secret variable in Azure DevOps. Never put it in the repository.
3. Plan for the settings that aren't files. Each README lists them: a variable group, an environment named `prod` with an approval and an exclusive lock, and a build validation policy on `main`.

## What was tested

Both examples ran on Azure DevOps Services with Microsoft-hosted `ubuntu-24.04` agents against DataRobot cloud (US).

- The workload example: a pull request plan, a merge, the approval, the deploy, and a smoke test, for the Python and the Spring Boot sample.
- The Custom Application example: a first deploy, an update, a pull request plan with no changes, and the Pulumi state lock on Azure Blob Storage.

Not tested: a self-hosted agent, Azure DevOps Server, a network without access to GitHub, and a DataRobot release other than the cloud release used for testing. Each README marks its unverified steps.

## Things to know

Two points affect how the examples behave.

- The Custom Application example needs a DataRobot release that can build an image from a Docker context. The README in that folder describes the resources it creates.
- One pipeline step sets a fixed file time on the app folder. It stops every run from planning a rebuild. Remove it after a `datarobot` provider release that sets a fixed archive time ([terraform-provider-datarobot#438](https://github.com/datarobot-community/terraform-provider-datarobot/pull/438)).

## Troubleshooting

[TROUBLESHOOTING.md](TROUBLESHOOTING.md) lists the failures seen while running the examples, with the cause and the fix for each.

## License

Apache License 2.0. See [LICENSE](LICENSE).
