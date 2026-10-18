# DataRobot deploy examples for Azure DevOps

Example Azure DevOps pipelines that deploy an app to DataRobot. Each example is a self-contained folder to copy into a repository and adapt. A pull request prints the deployment plan. A merge to `main` waits for an approval, deploys the app, and runs a smoke test.

## Choose an example

The two examples differ in the DataRobot resource they create. Choose by what the DataRobot release supports. The following table compares them.

| Example | Deploys | Use it when |
| --- | --- | --- |
| [`templates/azure-devops-workload`](templates/azure-devops-workload/README.md) | A container as a DataRobot Workload, with `dr workload up`. | The DataRobot release has Workloads. |
| [`templates/azure-devops-custom-app`](templates/azure-devops-custom-app/README.md) | A container as a Custom Application, with Pulumi and the state in Azure Blob Storage. | The release has no Workloads, or Custom Applications already run. |

Both examples include a small Spring Boot sample app. The workload example also includes a Python sample.

To check what a release supports, run `scripts/check_workload_ready.py`. The script reads what the DataRobot account allows and changes nothing. It needs `uv` or Python 3 (3.12 is the tested version), and the DataRobot endpoint and an API key in the environment:

```sh
export DATAROBOT_ENDPOINT=https://app.datarobot.com/api/v2
export DATAROBOT_API_TOKEN=<apiKey>
uv run scripts/check_workload_ready.py
```

## Adopt an example

Treat the chosen folder as the root of its own repository. To adopt it, follow these steps:

1. Copy the contents of the folder, not the folder itself, into a new Azure Repos repository.
2. Replace the sample app with the app to deploy.
3. Create the settings that aren't files, as the `README.md` in the folder describes: a variable group named `datarobot-deploy`, an environment named `prod` with an Approval check and an Exclusive lock, and a build validation policy on `main`.

Use the API key of a service account, not a person, and store it as a secret variable in the variable group. Never put it in the repository.

## How the pipelines work

Both pipelines have a Plan stage and an Apply stage:

- A pull request runs the Plan stage only. It prints what the deployment would change.
- A push to `main` that changes the app runs the Plan stage, then the Apply stage. The Apply stage waits for an approval on the `prod` environment, deploys the app, and calls `/hello` on it until the app answers with HTTP 200.

## What was tested

Both examples ran on Azure DevOps Services with Microsoft-hosted agents against a DataRobot cloud environment:

- **Workload example.** A pull request plan, a merge, the approval, the deploy, and a smoke test, for the Python and the Spring Boot sample.
- **Custom Application example.** A first deploy, an update, a pull request plan with no changes, and the Pulumi state lock on Azure Blob Storage.

The examples weren't tested with a self-hosted agent, Azure DevOps Server, a network without access to GitHub, or a self-managed DataRobot installation. Each example README marks its unverified steps.

## Limitations

These limitations affect how the examples behave:

- The Custom Application example needs a DataRobot release that can build an image from a Docker context. Its README describes the resources it creates.
- One pipeline step of the Custom Application example sets a fixed file time on the app folder, so that an unchanged app doesn't plan a rebuild on every run. Remove the step after a `datarobot` provider release that sets a fixed archive time ([terraform-provider-datarobot#438](https://github.com/datarobot-community/terraform-provider-datarobot/pull/438)).

## Troubleshooting

For failed or stuck runs, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md). It lists each failure with its cause and fix.

## Contributing

To report a problem or propose a change, see [CONTRIBUTING.md](CONTRIBUTING.md). AI coding agents, and people who adopt the examples, can start with [AGENTS.md](AGENTS.md). To report a vulnerability, see [SECURITY.md](SECURITY.md).

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE).
